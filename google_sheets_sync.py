"""
Google Sheets synchronization module for availability management.
Handles bidirectional sync between Google Sheets and PostgreSQL database.
"""

import gspread
from google.oauth2.service_account import Credentials
import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsSync:
    """Handles synchronization between Google Sheets and database."""
    
    def __init__(self, credentials_path: str, sheet_id: str, worksheet_name: str = "Sheet1"):
        """
        Initialize Google Sheets sync service.
        
        Args:
            credentials_path: Path to service account JSON credentials file
            sheet_id: Google Sheet ID
            worksheet_name: Name of the worksheet (default: "Sheet1")
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.worksheet_name = worksheet_name
        self.client = None
        self.sheet = None
        self.worksheet = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client."""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Try to load credentials from environment variables first (for Render/cloud deployments)
            gcp_type = os.getenv("GCP_TYPE")
            gcp_project_id = os.getenv("GCP_PROJECT_ID")
            gcp_private_key_id = os.getenv("GCP_PRIVATE_KEY_ID")
            gcp_private_key = os.getenv("GCP_PRIVATE_KEY")
            gcp_client_email = os.getenv("GCP_CLIENT_EMAIL")
            gcp_client_id = os.getenv("GCP_CLIENT_ID")
            
            if all([gcp_type, gcp_project_id, gcp_private_key_id, gcp_private_key, gcp_client_email, gcp_client_id]):
                # Load from environment variables
                # Strip quotes if present and replace escaped newlines in private_key
                private_key = gcp_private_key.strip('"\'')
                private_key = private_key.replace('\\n', '\n')
                
                creds_dict = {
                    "type": gcp_type,
                    "project_id": gcp_project_id,
                    "private_key_id": gcp_private_key_id,
                    "private_key": private_key,
                    "client_email": gcp_client_email,
                    "client_id": gcp_client_id,
                    "auth_uri": os.getenv("GCP_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                    "token_uri": os.getenv("GCP_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                    "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                    "client_x509_cert_url": os.getenv("GCP_CLIENT_X509_CERT_URL", ""),
                    "universe_domain": os.getenv("GCP_UNIVERSE_DOMAIN", "googleapis.com")
                }
                
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                logger.info("Loaded Google Sheets credentials from environment variables")
            elif os.path.exists(self.credentials_path):
                # Fallback to file (for local development)
                creds = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=scope
                )
                logger.info(f"Loaded Google Sheets credentials from file: {self.credentials_path}")
            else:
                raise FileNotFoundError(
                    f"Google Sheets credentials not found. Either set GCP_* environment variables "
                    f"or provide file at {self.credentials_path}"
                )
            
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.sheet_id)
            self.worksheet = self.sheet.worksheet(self.worksheet_name)
            logger.info(f"Successfully connected to Google Sheet: {self.sheet_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    def read_availability_data(self) -> List[Dict]:
        """
        Read all availability data from Google Sheet.
        
        Returns:
            List of dictionaries with keys: name, office_number, availability_status
        """
        try:
            # Get all values from the worksheet
            all_values = self.worksheet.get_all_values()
            
            if not all_values:
                logger.warning("Google Sheet is empty")
                return []
            
            # Assume first row is header
            # Expected columns: Name (नाव) | Office Number (कार्यालय क्रमांक) | Availability Status (उपलब्धता)
            header = all_values[0] if all_values else []
            
            # Find column indices (case-insensitive)
            name_col = None
            office_col = None
            status_col = None
            
            for idx, col in enumerate(header):
                col_lower = col.lower()
                # Match name column
                if 'नाव' in col or ('name' in col_lower and 'availability' not in col_lower):
                    if name_col is None:  # Take first match
                        name_col = idx
                # Match office column
                elif 'कार्यालय क्रमांक' in col or ('office' in col_lower and 'availability' not in col_lower) or ('room' in col_lower and 'availability' not in col_lower):
                    if office_col is None:  # Take first match
                        office_col = idx
                # Match status column - be more specific to avoid matching instruction column
                elif ('उपलब्धता' in col or ('availability' in col_lower and 'status' in col_lower)) and 'click' not in col_lower and 'dropdown' not in col_lower:
                    if status_col is None:  # Take first match
                        status_col = idx
            
            # If header not found, assume first 3 columns
            if name_col is None:
                name_col = 0
            if office_col is None:
                office_col = 1
            if status_col is None:
                status_col = 2
            
            # Parse data rows
            data = []
            for row_idx, row in enumerate(all_values[1:], start=2):  # Start from row 2 (after header)
                if len(row) <= max(name_col, office_col, status_col):
                    continue
                
                name = row[name_col].strip() if name_col < len(row) else ""
                office_number = row[office_col].strip() if office_col < len(row) else ""
                status_text = row[status_col].strip() if status_col < len(row) else ""
                
                # Skip empty rows
                if not name and not office_number:
                    continue
                
                # Parse availability status
                # Check for unavailable indicators first (more specific)
                status_lower = status_text.lower()
                
                # Check for unavailable markers (X mark, red X, or unavailable text)
                has_unavailable_marker = (
                    '❌' in status_text or
                    'unavailable' in status_lower or
                    'अनुपलब्ध' in status_text or
                    status_text.startswith('X ') or  # Handle "X Unavailable" format
                    status_text.startswith('x ')
                )
                
                # If no unavailable marker, check for available markers
                if has_unavailable_marker:
                    is_available = False
                else:
                    # Check for available markers (checkmark, available text)
                    is_available = (
                        '✅' in status_text or
                        'available' in status_lower or
                        'उपलब्ध' in status_text or
                        status_lower in ['yes', 'true', '1', 'y', 'on'] or
                        status_text.startswith('✔')  # Alternative checkmark
                    )
                
                data.append({
                    'name': name,
                    'office_number': office_number,
                    'availability_status': status_text,
                    'is_available': is_available,
                    'row_number': row_idx
                })
            
            logger.info(f"Read {len(data)} rows from Google Sheet")
            return data
            
        except Exception as e:
            logger.error(f"Error reading availability data from sheet: {e}")
            raise
    
    def find_row_by_person(self, name: str, office_number: str) -> Optional[int]:
        """
        Find row number for a person by name and office number.
        
        Args:
            name: Person's name
            office_number: Office number
            
        Returns:
            Row number (1-indexed) or None if not found
        """
        try:
            all_values = self.worksheet.get_all_values()
            if not all_values:
                return None
            
            # Find column indices
            header = all_values[0]
            name_col = None
            office_col = None
            
            for idx, col in enumerate(header):
                col_lower = col.lower()
                if 'नाव' in col or 'name' in col_lower:
                    name_col = idx
                elif 'कार्यालय क्रमांक' in col or 'office' in col_lower or 'room' in col_lower:
                    office_col = idx
            
            if name_col is None:
                name_col = 0
            if office_col is None:
                office_col = 1
            
            # Search for matching row
            name_clean = name.strip() if name else ""
            office_clean = office_number.strip() if office_number else ""
            
            for row_idx, row in enumerate(all_values[1:], start=2):
                if len(row) <= max(name_col, office_col):
                    continue
                
                row_name = row[name_col].strip() if name_col < len(row) else ""
                row_office = row[office_col].strip() if office_col < len(row) else ""
                
                # Match by office_number first (most reliable identifier)
                office_match = (
                    office_clean == row_office or
                    office_clean in row_office or
                    row_office in office_clean
                )
                
                if not office_match:
                    continue
                
                # If both have names, match by name too
                if name_clean and row_name:
                    name_match = (
                        name_clean.lower() == row_name.lower() or
                        name_clean.lower() in row_name.lower() or
                        row_name.lower() in name_clean.lower()
                    )
                    if name_match:
                        return row_idx
                # If both are empty/---, match by office only
                elif (not name_clean or name_clean == '---') and (not row_name or row_name == '---'):
                    return row_idx
                # If one has name and other doesn't, don't match (to avoid false matches)
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding row for person {name}, {office_number}: {e}")
            return None
    
    def update_availability(self, name: str, office_number: str, is_available: bool) -> bool:
        """
        Update availability status for a specific person in Google Sheet.
        
        Args:
            name: Person's name
            office_number: Office number
            is_available: New availability status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            row_num = self.find_row_by_person(name, office_number)
            if not row_num:
                logger.warning(f"Person not found in sheet: {name}, {office_number}")
                return False
            
            # Find status column
            all_values = self.worksheet.get_all_values()
            header = all_values[0] if all_values else []
            status_col = None
            
            for idx, col in enumerate(header):
                col_lower = col.lower()
                if 'उपलब्धता' in col or 'availability' in col_lower or 'status' in col_lower:
                    status_col = idx
                    break
            
            if status_col is None:
                status_col = 2  # Default to 3rd column
            
            # Update the cell (gspread uses 1-indexed for both row and col)
            status_text = "✅ Available / उपलब्ध" if is_available else "❌ Unavailable / अनुपलब्ध"
            # Use update_cell(row, col, value) - both row and col are 1-indexed
            self.worksheet.update_cell(row_num, status_col + 1, status_text)
            
            logger.info(f"Updated availability for {name} ({office_number}) to {status_text}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating availability in sheet: {e}")
            return False
    
    def sync_sheet_to_db(self, db_connection_func) -> Tuple[int, int, List[str]]:
        """
        Sync data from Google Sheet to database.
        
        Args:
            db_connection_func: Function that returns a database connection
            
        Returns:
            Tuple of (updated_count, error_count, error_messages)
        """
        updated_count = 0
        error_count = 0
        error_messages = []
        
        try:
            # Read data from sheet
            sheet_data = self.read_availability_data()
            
            if not sheet_data:
                logger.info("No data to sync from sheet")
                return (0, 0, [])
            
            # Get database connection
            conn = db_connection_func()
            if not conn:
                error_messages.append("Database connection failed")
                return (0, 1, error_messages)
            
            try:
                cursor = conn.cursor()
                
                for item in sheet_data:
                    try:
                        name = item['name'].strip() if item['name'] else ""
                        office_number = item['office_number'].strip() if item['office_number'] else ""
                        is_available = item['is_available']
                        
                        # Skip if both name and office_number are empty
                        if not name and not office_number:
                            continue
                        
                        # Match by office_number first (most reliable identifier)
                        # Use exact match for office_number to avoid false matches
                        if not office_number:
                            error_messages.append(f"Cannot match: missing office_number for '{name}'")
                            error_count += 1
                            continue
                        
                        # Try exact match first
                        if name and name != '---':
                            # Match by both name and office_number (exact match)
                            cursor.execute("""
                                UPDATE persons 
                                SET is_available = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE office_number = %s AND name = %s
                            """, (is_available, office_number, name))
                            
                            if cursor.rowcount > 0:
                                updated_count += 1
                                continue
                            
                            # Try flexible name matching
                            cursor.execute("""
                                UPDATE persons 
                                SET is_available = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE office_number = %s AND name ILIKE %s
                            """, (is_available, office_number, f"%{name}%"))
                            
                            if cursor.rowcount > 0:
                                updated_count += 1
                                continue
                        
                        # Match by office_number only (for rows with empty/null names)
                        cursor.execute("""
                            UPDATE persons 
                            SET is_available = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE office_number = %s AND (name IS NULL OR name = '' OR name = '---' OR name = 'N/A')
                        """, (is_available, office_number))
                        
                        if cursor.rowcount > 0:
                            updated_count += 1
                        else:
                            error_messages.append(f"Person not found: name='{name}', office='{office_number}'")
                            error_count += 1
                                
                    except Exception as e:
                        error_messages.append(f"Error updating {item.get('name', 'unknown')}: {str(e)}")
                        error_count += 1
                        logger.error(f"Error syncing person {item.get('name')}: {e}")
                
                conn.commit()
                cursor.close()
                
            finally:
                conn.close()
            
            logger.info(f"Sync completed: {updated_count} updated, {error_count} errors")
            return (updated_count, error_count, error_messages)
            
        except Exception as e:
            logger.error(f"Error syncing sheet to database: {e}")
            error_messages.append(f"Sync error: {str(e)}")
            return (0, 1, error_messages)
    
    def sync_db_to_sheet(self, db_connection_func) -> Tuple[int, int, List[str]]:
        """
        Sync data from database to Google Sheet.
        Creates rows if they don't exist, updates if they do.
        
        Args:
            db_connection_func: Function that returns a database connection
            
        Returns:
            Tuple of (updated_count, error_count, error_messages)
        """
        updated_count = 0
        error_count = 0
        error_messages = []
        
        try:
            # Get database connection
            conn = db_connection_func()
            if not conn:
                error_messages.append("Database connection failed")
                return (0, 1, error_messages)
            
            try:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT name, office_number, is_available FROM persons")
                db_persons = cursor.fetchall()
                cursor.close()
                
            finally:
                conn.close()
            
            # Ensure header row exists
            all_values = self.worksheet.get_all_values()
            if not all_values or len(all_values) == 0:
                # Create header row
                self.worksheet.append_row([
                    "Name (नाव)",
                    "Office Number (कार्यालय क्रमांक)",
                    "Availability Status (उपलब्धता)"
                ])
            
            # Sync each person
            for person in db_persons:
                try:
                    name = person['name']
                    office_number = person['office_number'] or ""
                    is_available = person['is_available']
                    
                    # Check if row exists
                    row_num = self.find_row_by_person(name, office_number)
                    
                    if row_num:
                        # Update existing row
                        success = self.update_availability(name, office_number, is_available)
                        if success:
                            updated_count += 1
                        else:
                            error_count += 1
                            error_messages.append(f"Failed to update: {name}")
                    else:
                        # Add new row
                        status_text = "✅ Available / उपलब्ध" if is_available else "❌ Unavailable / अनुपलब्ध"
                        self.worksheet.append_row([name, office_number, status_text])
                        updated_count += 1
                        logger.info(f"Added new row for {name} ({office_number})")
                        
                except Exception as e:
                    error_messages.append(f"Error syncing {person.get('name', 'unknown')}: {str(e)}")
                    error_count += 1
                    logger.error(f"Error syncing person {person.get('name')}: {e}")
            
            logger.info(f"DB to Sheet sync completed: {updated_count} updated, {error_count} errors")
            return (updated_count, error_count, error_messages)
            
        except Exception as e:
            logger.error(f"Error syncing database to sheet: {e}")
            error_messages.append(f"Sync error: {str(e)}")
            return (0, 1, error_messages)
    
    def initialize_sheet(self, db_connection_func) -> Tuple[bool, str, int]:
        """
        Initialize Google Sheet with headers and populate with all data from database.
        This will clear existing data and set up the sheet from scratch.
        
        Args:
            db_connection_func: Function that returns a database connection
            
        Returns:
            Tuple of (success, message, rows_added)
        """
        try:
            # Get all persons from database
            conn = db_connection_func()
            if not conn:
                return (False, "Database connection failed", 0)
            
            try:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT name, office_number, is_available FROM persons ORDER BY name")
                db_persons = cursor.fetchall()
                cursor.close()
            finally:
                conn.close()
            
            # Clear existing worksheet data
            self.worksheet.clear()
            
            # Set up header row
            header = [
                "Name (नाव)",
                "Office Number (कार्यालय क्रमांक)",
                "Availability Status (उपलब्धता)"
            ]
            
            # Prepare all rows at once (header + data) for batch write
            all_rows = [header]
            for person in db_persons:
                name = person['name'] or ""
                office_number = person['office_number'] or ""
                is_available = person['is_available']
                
                # Use emoji indicators for easy visual identification
                status_text = "✅ Available / उपलब्ध" if is_available else "❌ Unavailable / अनुपलब्ध"
                all_rows.append([name, office_number, status_text])
            
            # Batch write all rows at once (much faster and avoids rate limits)
            self.worksheet.append_rows(all_rows)
            rows_added = len(all_rows) - 1  # Exclude header
            
            # Format header row (bold, background color) - simplified format
            try:
                # Make header row bold and colored (using correct API format)
                self.worksheet.format('A1:C1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'horizontalAlignment': 'CENTER'
                })
            except Exception as e:
                logger.warning(f"Could not format header row: {e}")
            
            # Set up data validation for Status column (Column C) to allow easy selection
            try:
                # Get the number of data rows (excluding header)
                num_rows = len(db_persons)
                if num_rows > 0:
                    # Create data validation rule for column C (Status column)
                    # Allow dropdown with two options: Available and Unavailable
                    validation_rule = {
                        'condition': {
                            'type': 'ONE_OF_LIST',
                            'values': [
                                {'userEnteredValue': '✅ Available / उपलब्ध'},
                                {'userEnteredValue': '❌ Unavailable / अनुपलब्ध'}
                            ]
                        },
                        'showCustomUi': True,
                        'strict': True
                    }
                    
                    # Apply validation to column C, rows 2 to num_rows+1
                    # Note: gspread uses 1-indexed, and we need to convert column C to number (3)
                    # We'll use batch_update for this
                    requests = [{
                        'setDataValidation': {
                            'range': {
                                'sheetId': self.worksheet.id,
                                'startRowIndex': 1,  # Row 2 (0-indexed, header is row 0)
                                'endRowIndex': num_rows + 1,  # Up to last data row
                                'startColumnIndex': 2,  # Column C (0-indexed: A=0, B=1, C=2)
                                'endColumnIndex': 3
                            },
                            'rule': validation_rule
                        }
                    }]
                    
                    self.sheet.batch_update({'requests': requests})
                    logger.info(f"Data validation set for {num_rows} rows in Status column")
            except Exception as e:
                logger.warning(f"Could not set data validation: {e}")
            
            # Add instruction note in cell D1
            try:
                self.worksheet.update('D1', '💡 Click dropdown in Status column to change availability. Changes sync every 1-2 minutes.')
                self.worksheet.format('D1', {
                    'textFormat': {'italic': True, 'fontSize': 9},
                    'backgroundColor': {'red': 1.0, 'green': 0.95, 'blue': 0.8}
                })
            except Exception as e:
                logger.warning(f"Could not add instruction note: {e}")
            
            # Note: Column widths can be adjusted manually in Google Sheets
            # The data is now populated and ready to use
            
            logger.info(f"Sheet initialized successfully with {rows_added} rows")
            return (True, f"Sheet initialized successfully with {rows_added} persons", rows_added)
            
        except Exception as e:
            logger.error(f"Error initializing sheet: {e}")
            return (False, f"Error: {str(e)}", 0)

