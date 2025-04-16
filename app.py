from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.security import check_password_hash
import pandas as pd
from gtts import gTTS
import io
import os
from dotenv import load_dotenv
from openai import OpenAI
import base64
from flask_cors import CORS

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for API access

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# Floor mapping from Marathi to English
floor_mapping = {
    "तळ": "ground",
    "पहिला": "first",
    "दुसरा": "second",
    "तिसरा": "third",
    "चौथा": "fourth",
    "पाचवा": "fifth",
    "सहावा": "sixth",
    "सातवा": "seventh",
}

# Common corrections for names
name_corrections = {
    "मुख्र्": "मुख्य",
    "हदपक": "दिपक",
    "प्रशाांत": "प्रशांत",
    "रुभ": "रूम",
    "नां.": "",
    "िुमाळ": "कुमार",
}
# Provided data
data = [
    {
        "पद": "पोस्टमास्तर - ग्रेड 2",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "जी -19",
        "नाव": "श्री सचिन बडे",
        "मोबाईल क्रमांक": "7021786749",
        "मजला": "तळ मजला",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "वैद्यकीय अधिकारी",
        "कार्यालयाचे नाव": "शासकीय दवाखाना, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "जी-14-15",
        "नाव": "डॉ. गणेश धुमाळ",
        "मोबाईल क्रमांक": "9819482852",
        "मजला": "तळ मजला",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "कोषागार अधिकारी सहायक संचालक",
        "कार्यालयाचे नाव": "उप कोषागार कार्यालय, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "जी 16",
        "नाव": "श्रीमती जास्मिन शेख",
        "मोबाईल क्रमांक": "8828054223",
        "मजला": "तळ मजला",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "सहायक पोलीस आयुक्त(वाहतूक)",
        "कार्यालयाचे नाव": "वाहतूक विभाग, नवी मुंबई",
        "कार्यालय क्रमांक": "जी -1",
        "नाव": "श्री विठठल कुबडे",
        "मोबाईल क्रमांक": "9764197977",
        "मजला": "तळ मजला",
        "शेरा": "मुख्य इमारत सिडको बाजू"
    },
    {
        "पद": "बालविकास प्रकल्प अधिकारी",
        "कार्यालयाचे नाव": "नागरी प्रकल्प तुर्भे-पनवेल, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "जी -17",
        "नाव": "श्रीमती ज्योती सदानंद पाटील",
        "मोबाईल क्रमांक": "9834985848",
        "मजला": "तळ मजला",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "सहचिटणीस / उपाध्यक्ष",
        "कार्यालयाचे नाव": "राज्य सरकारी कर्मचारी संघटना, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "जी- 20",
        "नाव": "श्री मोरश्वर चौधरी, श्रीमती अस्मिता जोशी",
        "मोबाईल क्रमांक": "9067772222, 7208367956",
        "मजला": "तळ मजला",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "अध्यक्ष",
        "कार्यालयाचे नाव": "शासकीय वाहन चालक संघटना, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "",
        "नाव": "श्री जनार्दन म्हात्रे",
        "मोबाईल क्रमांक": "8850143480, 9867671422",
        "मजला": "तळ मजला",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "उद्यान अधिक्षक",
        "कार्यालयाचे नाव": "उपवने व उद्याने, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "जी-08",
        "नाव": "श्री विशाल भोर",
        "मोबाईल क्रमांक": "8329358136",
        "मजला": "तळ मजला",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "अध्यक्ष",
        "कार्यालयाचे नाव": "जिल्हा जात प्रमाणपत्र पडताळणी समिती, ठाणे",
        "कार्यालय क्रमांक": "जी-09/10",
        "नाव": "श्रीमती रेवती गायकर",
        "मोबाईल क्रमांक": "8888282299",
        "मजला": "तळ मजला",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "मा.विभागीय आयुक्त",
        "कार्यालयाचे नाव": "कोकण विभाग यांचे दालन व स्वीय सहाय्यक कक्ष",
        "कार्यालय क्रमांक": "रूम नं . 101 व 101 अ",
        "नाव": "श्री. अभिजीत सावळे",
        "मोबाईल क्रमांक": "8108129955",
        "मजला": "पहिला मजला",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "अधिक्षक अभियंता",
        "कार्यालयाचे नाव": "संकल्प चित्र मंडळ (सा.बां.विभाग), कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-401 ते 406 (मुख्य इमारत), रूम नं. 412 ते 415 (जोड इमारत सिडको बाजू), रूम नं. 416 ते 419 (जोड इमारत पनवेल बाजू)",
        "नाव": "श्री शाम सु. गांगुर्डे",
        "मोबाईल क्रमांक": "7710004878",
        "मजला": "चौथा",
        "शेरा": "मुख्य / जोड इमारत सिडको व पनवेल बाजू"
    },
    {
        "पद": "अधिक्षक अभियंता",
        "कार्यालयाचे नाव": "संकल्प चित्र मंडळ (सा.बां.विभाग), ग्रंथालय, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-409 ते 411 (मुख्य इमारत)",
        "नाव": "श्री शाम सु. गांगुर्डे",
        "मोबाईल क्रमांक": "7710004878",
        "मजला": "चौथा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "अधिक्षक अभियंता",
        "कार्यालयाचे नाव": "दक्षता व गुणनियंत्रण मंडळ, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-515, 516, 518",
        "नाव": "श्री सुरेंद्र लक्ष्मण टोपले",
        "मोबाईल क्रमांक": "9869334390",
        "मजला": "पाचवा",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "कार्यकारी संचालक",
        "कार्यालयाचे नाव": "महाराष्ट्र उद्योजकता विकास केंद्र, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-512",
        "नाव": "श्री दत्तात्रय थावरे",
        "मोबाईल क्रमांक": "9403078766",
        "मजला": "पाचवा",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "अधिक्षक अभियंता",
        "कार्यालयाचे नाव": "रायगड (सा.बां.) मंडळ, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-501, 502, 503, 510",
        "नाव": "श्रीमती सुषमा गायकवाड",
        "मोबाईल क्रमांक": "9967014557",
        "मजला": "पाचवा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "प्रादेशिक दुग्धव्यवसाय विकास अधिकारी",
        "कार्यालयाचे नाव": "मुंबई विभाग, कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-511, 513, 514",
        "नाव": "श्री हेमंत जी गडवे",
        "मोबाईल क्रमांक": "9545370007",
        "मजला": "पाचवा",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
        {
        "पद": "सह संचालक अर्थ व सांख्यिकी संचालनालय",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.- 715 , 716",
        "नाव": "श्रीमती सीमा प्र. जोशी",
        "मोबाईल क्रमांक": "9764068320",
        "मजला": "सातवा",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "कार्यकारी अभियंता ठाणे खाडीपूल विभाग क्र.01",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-706",
        "नाव": "श्रीमती स्वाती पाठक, श्री सुभाष ढा. आढे",
        "मोबाईल क्रमांक": "8369421295, 9821359054",
        "मजला": "सातवा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "उप संचालक भूजल सर्वेक्षण आणि विकास यंत्रणा",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-708 ते 710",
        "नाव": "श्री नितीन पुरषोत्तम दहिकर",
        "मोबाईल क्रमांक": "9623641368",
        "मजला": "सातवा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "पोलीस अधिक्षक राज्य गुन्हे अन्वेषण विभाग, गुन्हे शाखा",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-701,702",
        "नाव": "श्री प्रशांत विजयकुमार वाघुंडे",
        "मोबाईल क्रमांक": "8975112999",
        "मजला": "सातवा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "अधिक्षक अभियंता(यांत्रिकी) सार्वजनिक बांधकाम विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-704,705",
        "नाव": "श्री राजेंद्र हरी चव्हाण",
        "मोबाईल क्रमांक": "8108381266",
        "मजला": "सातवा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "सह संचालक आरोग्य सेवा (हिवताप) मुंबई विभाग, ठाणे",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-628",
        "नाव": "डॉ. बाळासाहेब संभाजीराव सोनावणे",
        "मोबाईल क्रमांक": "9920568715",
        "मजला": "सहावा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "मुख्य कार्यकारी अधिकारी, महाराष्ट्र राज्य ग्रामीण जीवनोन्नती अभियान, राज्य अभियान व्यवस्थापन कक्ष",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-627",
        "नाव": "",
        "मोबाईल क्रमांक": "",
        "मजला": "सहावा",
        "शेरा": "विस्तार इमारत (कार्यालय बंद आहे)"
    },
    {
        "पद": "पोलीस उप अधिक्षक बिनतारी संदेश, कोकण परिक्षेत्र",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-626",
        "नाव": "श्रीमती आर. वाय. सावंत",
        "मोबाईल क्रमांक": "9270352540",
        "मजला": "सहावा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "विभागीय सह निबंधक सहकारी संस्था (लेखा परीक्षण) मुंबई विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-621",
        "नाव": "श्री. तुषार काकडे",
        "मोबाईल क्रमांक": "9892035321",
        "मजला": "सहावा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "अधीक्षक अभियंता राष्ट्रीय महामार्ग मंडळ",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-622 ते 624",
        "नाव": "श्रीमती तृप्ती ब्रि. नाग",
        "मोबाईल क्रमांक": "8452929555",
        "मजला": "सहावा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "प्रादेशिक उपायुक्त, समाजकल्याण मुंबई विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-619, 620",
        "नाव": "श्री बाळासाहेब सोळंकी",
        "मोबाईल क्रमांक": "8378088188",
        "मजला": "सहावा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "सह नियंत्रक वैध मापन शास्त्र, कोकण विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-625",
        "नाव": "श्री शिवसिंह काकडे",
        "मोबाईल क्रमांक": "9833269900",
        "मजला": "सहावा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "पोलीस उप आयुक्त (वाहतूक) नवी मुंबई पोलीस आयुक्तालय",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-732",
        "नाव": "श्री तिरुपती काकडे",
        "मोबाईल क्रमांक": "9158910100",
        "मजला": "सातवा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "मा.आयुक्त, राज्य सेवा हक्क आयोग, कोकण महसूली विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-727 व 721 क",
        "नाव": "श्री बलदेव सिंग",
        "मोबाईल क्रमांक": "9702200700",
        "मजला": "सातवा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "उपसंचालक, पर्यटन संचालनालय",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-721 अ",
        "नाव": "श्री हनुमंत कृ. हेडे",
        "मोबाईल क्रमांक": "9604328000",
        "मजला": "सातवा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "स्थानिक निधी लेखापरीक्षा कार्यालय, अभिलेख कक्ष",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-720",
        "नाव": "",
        "मोबाईल क्रमांक": "",
        "मजला": "सातवा",
        "शेरा": "विस्तार इमारत"
    },
    {
        "पद": "विशेष पोलीस महानिरीक्षक कोकण परिक्षेत्र",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-601,602",
        "नाव": "श्री. संजय रूख्मिणी भास्कर दराडे",
        "मोबाईल क्रमांक": "9823133910",
        "मजला": "सहावा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "सह संचालक (मनपालेव) स्थानिक निधी लेखापरीक्षा",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-603,608,610",
        "नाव": "श्री धनंजय आंधळे",
        "मोबाईल क्रमांक": "9403969098",
        "मजला": "सहावा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "कनिष्ठ वैज्ञानिक अधिकारी सार्वजनिक आरोग्य प्रयोगशाळा",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-606",
        "नाव": "श्री अरविंद जगन्नाथ देसाई",
        "मोबाईल क्रमांक": "9702280885",
        "मजला": "सहावा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "राज्य कर सह आयुक्त (जीएसटी प्रशासन) रायगड विभाग बेलापूर",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-611 ते 614",
        "नाव": "श्री विनोद रामचंद्र देसाई",
        "मोबाईल क्रमांक": "9967571885",
        "मजला": "सहावा",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "राज्यकर सह आयुक्त (जीएसटी प्रशासन) रायगड विभाग बेलापूर",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-615 ते 618",
        "नाव": "",
        "मोबाईल क्रमांक": "",
        "मजला": "सहावा",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "राज्य कर सह आयुक्त (जीएसटी प्रशासन) रायगड विभाग बेलापूर",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-711 ते 714",
        "नाव": "",
        "मोबाईल क्रमांक": "",
        "मजला": "सातवा",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
    "पद": "उपविभागीय अधिकारी सार्वजनिक बांधकाम उपविभाग",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.- जी 28",
    "नाव": "श्री राहुल नामदेव चव्हाण",
    "मोबाईल क्रमांक": "9423378892",
    "मजला": "तळ मजला",
    "शेरा": "विस्तार इमारत पनवेल बाजू"
    },
    {
    "पद": "व्यवस्थापक कोकण भवन उपहारगृह",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-122",
    "नाव": "श्री रवि फ. नागरे",
    "मोबाईल क्रमांक": "9922289899",
    "मजला": "पहिला मजला",
    "शेरा": "विस्तार इमारत सिडको/पनवेल बाजू"
    },
    {
    "पद": "मतदार नोंदणी अधिकारी 151 बेलापूर विधानसभा मतदार संघ",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-121",
    "नाव": "श्रीमती आश्विनी सुर्वे पाटील",
    "मोबाईल क्रमांक": "989008775",
    "मजला": "पहिला मजला",
    "शेरा": "विस्तार इमारत पनवेल बाजू"
    },
    {
    "पद": "सह.दुय्यम निबंधक वर्ग -2 ठाणे क्र-6, बेलापूर",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-123",
    "नाव": "श्रीमती विद्या विजय जाधव",
    "मोबाईल क्रमांक": "9777535046",
    "मजला": "पहिला मजला",
    "शेरा": "विस्तार इमारत सिडको बाजू"
    },
    {
    "पद": "शाखा व्यवस्थापक दि महाराष्ट्र मंत्रालय ॲन्ड अलाईड ऑफीसेस को.ऑप.बँक लि.",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-224",
    "नाव": "श्रीमती पुनम देशपांडे",
    "मोबाईल क्रमांक": "9819196165",
    "मजला": "दुसरा मजला",
    "शेरा": "विस्तार इमारत सिडको बाजू"
    },
    {
    "पद": "जिल्हा दुग्धव्यवसाय विकास अधिकारी ठाणे",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-221",
    "नाव": "श्रीमती लक्ष्मी मेश्राम",
    "मोबाईल क्रमांक": "8108477274",
    "मजला": "दुसरा मजला",
    "शेरा": "विस्तार इमारत"
    },
    {
    "पद": "अपर उप आयुक्त राज्य गुप्त वार्ता विभाग कोकण घटक",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-222 व 223",
    "नाव": "श्रीमती यशोधरा गोडबोले",
    "मोबाईल क्रमांक": "9821714262",
    "मजला": "दुसरा मजला",
    "शेरा": "विस्तार इमारत"
    },
    {
    "पद": "आयुक्त, कौशल्य विकास, रोजगार व उद्योजकता विभागीय आयुक्तालय, मुंबई विभाग",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-322 ते 328",
    "नाव": "श्री नितीन पाटील (IAS), श्री. दि. दे. पवार",
    "मोबाईल क्रमांक": "9324829136, 9892794331",
    "मजला": "तिसरा मजला",
    "शेरा": "विस्तार इमारत"
    },
    {
    "पद": "कार्यकारी अभियंता कोकण संकल्प चित्र विभाग",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-319 ते 321",
    "नाव": "श्री एस डी जाधव",
    "मोबाईल क्रमांक": "9029165504",
    "मजला": "तिसरा मजला",
    "शेरा": "विस्तार इमारत"
    },
    {
    "पद": "अध्यक्ष ठाणे अतिरिक्त जिल्हा ग्राहक तक्रार निवारण आयोग",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-428, 429",
    "नाव": "श्री तुषार सोनकुदळे, श्री उमेश स. चव्हाण",
    "मोबाईल क्रमांक": "9820136122, 9920412058",
    "मजला": "चौथा मजला",
    "शेरा": "विस्तार इमारत"
    },
    {
    "पद": "सहसचिव तथा प्रादेशिक चौकशी अधिकारी कोकण विभाग",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-420",
    "नाव": "श्री कैलास बधान",
    "मोबाईल क्रमांक": "9702088422",
    "मजला": "चौथा मजला",
    "शेरा": "विस्तार इमारत"
    },
    {
    "पद": "महाराष्ट्र राज्य माहिती आयोग, कोकण खंडपीठ",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-527, 528",
    "नाव": "श्री शेखर चन्ने, श्रीमती रीना फणसेकर",
    "मोबाईल क्रमांक": "9833620113, 9969075742",
    "मजला": "पाचवा मजला",
    "शेरा": "विस्तार इमारत"
    },
    {
    "पद": "मुख्य अभियंता राष्ट्रीय महामार्ग (सा.बां.), महाराष्ट्र",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-523 ते 526",
    "नाव": "श्री संतोष ग. शेलार",
    "मोबाईल क्रमांक": "9689499999",
    "मजला": "पाचवा मजला",
    "शेरा": "विस्तार इमारत"
    },
    {
    "पद": "मा.विभागीय आयुक्त, कोकण विभाग यांचे दालन व स्वीय सहाय्यक कक्ष",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-101 व 101 अ",
    "नाव": "श्री. अभिजीत सावळे",
    "मोबाईल क्रमांक": "8108129955",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "आपत्ती व्यवस्थापन नियंत्रण कक्ष",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-102",
    "नाव": "श्रीमती वैशाली इंदाणी उंटवाल अपर आयुक्त (महसूल)",
    "मोबाईल क्रमांक": "9422607907",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "महसूल शाखा",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-104",
    "नाव": "श्रीमती वैशाली इंदाणी उंटवाल अपर आयुक्त (महसूल)",
    "मोबाईल क्रमांक": "9422607907",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "सामान्य प्रशासन शाखा",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-106",
    "नाव": "श्रीमती राजलक्ष्मी शाह अपर आयुक्त (सामान्य प्रशासन)",
    "मोबाईल क्रमांक": "9890452740",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "विकास शाखा",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-110",
    "नाव": "श्री. प्रदिप घोरपडे प्रभारी उपायुक्त",
    "मोबाईल क्रमांक": "8108313555",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "विकास आस्थापना",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-111",
    "नाव": "श्रीमती मिनल कुटे",
    "मोबाईल क्रमांक": "9096390700",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "महसूल-आस्थापना शाखा",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-113",
    "नाव": "श्रीमती वैशाली इंदाणी उंटवाल",
    "मोबाईल क्रमांक": "9422607907",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "करमणूक शुल्क शाखा",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-117",
    "नाव": "श्री. संजीव पलांडे",
    "मोबाईल क्रमांक": "9136106770",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "लेखामेळ शाखा",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-118",
    "नाव": "श्री. दिपक काटे",
    "मोबाईल क्रमांक": "9082790027",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
    "पद": "नगरपालिका प्रशासन शाखा",
    "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
    "कार्यालय क्रमांक": "रूम नं.-119",
    "नाव": "श्री. गणेश शेटे",
    "मोबाईल क्रमांक": "9850573739",
    "मजला": "पहिला मजला",
    "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "जिल्हा उप निबंधक सहकारी संस्था (2) पूर्व उपनगरे मुंबई",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-201",
        "नाव": "श्री नितीन दहिभाते जिल्हा उप निबंधक",
        "मोबाईल क्रमांक": "9785180696",
        "मजला": "दुसरा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "उप निबंधक सहकारी संस्था (एम विभाग) व सहायक निबंधक सहकारी संस्था एस विभाग, मुंबई",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-202",
        "नाव": "श्री सुनिल बनसोडे उप निबंधक सहकारी संस्था (एम विभाग), श्री अजयकुमार भालके (एम विभाग)",
        "मोबाईल क्रमांक": "9975085806, 9324262877",
        "मजला": "दुसरा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "वस्तू व सेवा कर विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं. 203 ते 210",
        "नाव": "",
        "मोबाईल क्रमांक": "",
        "मजला": "दुसरा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "राज्यकर सह आयुक्त , वस्तू व सेवा कर",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं. 211 व 212",
        "नाव": "",
        "मोबाईल क्रमांक": "",
        "मजला": "दुसरा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "सहायक ग्रंथालय संचालक मुंबई विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-218",
        "नाव": "श्री प्रशांत पाटील सहाय्यक ग्रंथालय संचालक",
        "मोबाईल क्रमांक": "9022074560",
        "मजला": "दुसरा",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "दि महाराष्ट्र मंत्रालय व संलग्न शासकीय कर्मचारी को.ऑपरेटिव्ह क्रेडीट सोसायटी",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-217",
        "नाव": "श्री महेंद्र वा. पडवळ सहायक व्यवस्थापक",
        "मोबाईल क्रमांक": "977377881",
        "मजला": "दुसरा",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "सहायक संचालक नगररचना(मुल्यांकन) ठाणे",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-213",
        "नाव": "श्री रविंद्र पांडूरंग बनसोडे नगर रचनाकार",
        "मोबाईल क्रमांक": "9422425085",
        "मजला": "दुसरा",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "शासकीय पुर्ननियुक्त माजी सैनिक संघटना, महाराष्ट्र",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं 214",
        "नाव": "श्री अजित न्यायनिर्गुणे",
        "मोबाईल क्रमांक": "9969251300",
        "मजला": "दुसरा",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "कार्यकारी अभियंता रायगड पाटबंधारे विभाग क्र.02",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-301/302",
        "नाव": "श्री संजीव जाधव कार्यकारी अभियंता",
        "मोबाईल क्रमांक": "9029165504",
        "मजला": "तिसरा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "कनिष्ठ वैज्ञानिक अधिकारी सार्वजनिक आरोग्य प्रयोगशाळा (पाणी नमूने तपासणी)",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-307",
        "नाव": "श्री अरविंद जगन्नाथ देसाई कनिष्ठ वैज्ञानिक अधिकारी",
        "मोबाईल क्रमांक": "9702280885",
        "मजला": "तिसरा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "विभागीय सहनिबंधक सहकारी संस्था कोकण विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-308/309/310",
        "नाव": "श्री मिलींद सेन भालेराव विभागीय सहनिबंधक",
        "मोबाईल क्रमांक": "9527821642",
        "मजला": "तिसरा",
        "शेरा": "मुख्य इमारत"
    },
    {
        "पद": "सह संचालक नगररचना कोकण विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-305",
        "नाव": "श्री श्रीकांत देशमुख सह संचालक नगररचना",
        "मोबाईल क्रमांक": "9423035003",
        "मजला": "तिसरा",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "विभागीय सहायक भाषा संचालक , भाषा संचालनालय कोकण विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-315",
        "नाव": "श्री योगेश शेटये विभागीय सहायक भाषा संचालक",
        "मोबाईल क्रमांक": "9869126872",
        "मजला": "तिसरा",
        "शेरा": "जोड इमारत पनवेल बाजू"
    },
    {
        "पद": "उप संचालक भूजल सर्वेक्षण आणि विकास यंत्रणा ( प्रयोगशाळा )",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-312 ते 314",
        "नाव": "श्री नितीन पुरषोत्तम दहिकर उप संचालक भूजल सर्वेक्षण आणि विकास यंत्रणा",
        "मोबाईल क्रमांक": "9623641368",
        "मजला": "तिसरा",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "उप उपनिबंधक सहकारी संस्था एल/एन विभाग, मुंबई कोकण विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-311",
        "नाव": "श्रीमती प्रियंका गाडीलकर उप उपनिबंधक (एल), श्री हरिश जगताप (एल), श्री शिरीष सपकाळ (एन)",
        "मोबाईल क्रमांक": "9823625000, 9071081772",
        "मजला": "तिसरा",
        "शेरा": "जोड इमारत सिडको बाजू"
    },
    {
        "पद": "उप संचालक(माहिती) विभागीय माहिती कार्यालय कोकण विभाग",
        "कार्यालयाचे नाव": "कोकण भवन, नवी मुंबई",
        "कार्यालय क्रमांक": "रूम नं.-317",
        "नाव": "श्रीमती अर्चना शंभरकर प्र.उपसंचालक (माहिती)",
        "मोबाईल क्रमांक": "9987037103",
        "मजला": "तिसरा",
        "शेरा": "जोड इमारत पनवेल बाजू"
    }
    
]

# Create DataFrame
df = pd.DataFrame(data)
df = df.rename(columns={
    "मजला": "मजला",
    "कार्यालयाचे नाव": "कार्यालयाचे नाव",
    "दूरध्वनी क्रमांक": "दूरध्वनी क्रमांक",
    "नाव": "कार्यालय प्रमुखाचे नाव",
    "मोबाईल क्रमांक": "मोबाईल क्रमांक",
    "शेरा": "शेरा",
    "रूम नं.": "रूम नं."
})

# Apply name corrections
df["कार्यालय प्रमुखाचे नाव"] = df["कार्यालय प्रमुखाचे नाव"].apply(
    lambda x: "".join([name_corrections.get(word, word) for word in str(x).split()]) if pd.notna(x) else x
)

# Authentication
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('userId')
        password = request.form.get('password')
        if user_id == 'admin' and password == '5555':  # Hardcoded for simplicity; use environment variables in production
            return redirect(url_for('directory'))
        return render_template('index.html', error="अवैध पासवर्ड. कृपया पुन्हा प्रयत्न करा.")
    return render_template('index.html')

# Directory page
@app.route('/directory')
def directory():
    return render_template('directory.html', departments=sorted(df["पद"].dropna().unique()), people=sorted(df["कार्यालय प्रमुखाचे नाव"].dropna().unique()))

# API endpoint for search
@app.route('/api/search', methods=['POST'])
def search():
    try:
        query = request.json.get('query')
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Filter data based on exact match of 'पद' or 'कार्यालय प्रमुखाचे नाव'
        filtered_data = df[
            (df["पद"].astype(str).str.contains(query, case=False, na=False)) |
            (df["कार्यालय प्रमुखाचे नाव"].astype(str).str.contains(query, case=False, na=False))
        ]
        
        if not filtered_data.empty:
            result = "\n".join(
                filtered_data.apply(
                    lambda row: "\n".join([f"- {k}: {v}" for k, v in row.dropna().items()]), axis=1
                )
            )
        else:
            result = "माहिती उपलब्ध नाही"
        
        audio_base64 = get_audio_file(result)
        return jsonify({"result": result, "audio": audio_base64})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to get audio file
def get_audio_file(text):
    try:
        tts = gTTS(text=text, lang='mr')
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        return base64.b64encode(audio_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error generating audio: {e}")
        return ""

# Audio endpoint (for compatibility)
@app.route('/get_audio', methods=['POST'])
def get_audio():
    try:
        data = request.json
        text = data.get('text', '')
        audio_base64 = get_audio_file(text)
        return jsonify({"audio": audio_base64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)