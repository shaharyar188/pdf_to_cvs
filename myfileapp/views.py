import os
import PyPDF2
import csv
import re
import fs
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,redirect
from . models import myuploadFile


def HomePage(request):
    return render(request, "dashboard.html")


def uploadPdf(request):
    return render(request, "upload-pdf.html")


def viewData(request):
    return render(request, "view-data.html")

# ============================here the process data is working here===============================

def extract_text_from_pdf(pdf_path):
     with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return ''.join(page.extract_text() for page in reader.pages)


def parse_rows(content):
    transaction_pattern = re.compile(r'(\d{2}/\d{2})\s+(.*?)([\d,]+\.\d{2})')
    matches = transaction_pattern.findall(content)
    rows = []
    for match in matches:
        date, description, amount = match
        transaction_type = classify_transaction(description)
        rows.append([date, description, amount, transaction_type])
    return rows


def classify_transaction(description):
    # List of Lenders
    lenders = ["CAN CAPITAL", "KAPITUS", "MULLIGAN", "RAPID", "Libertas", "Channel Partners", "GetBackd", "IOU", "PIRS", "Reliant", "WALL STREET", "Principis/Smartstep", "FUNDWORKS", "GCM (Greenwich)", "Kalamata", "Simply Funding", "VOX", "CORNELL", "EBF (Everest)", "Vader", "FORWARD", "FUNDFI", "KNIGHT", "Legend", "PAC Western Financial", "ADVANTAGE", "BIZFUND", "BMT Capital", "Money Well Group", "Narra", "Avion","Yellowstone", "Everyday", "Ondeck", "Paz Funding", "Epic ADVAN", "Fundbox", "YELLOW", "AVANZA", "Delta Bridge", "COBALT", "Coolidge Capital", "THOR Capital Group", "AMERIFI", "Arvi", "UFS", "Capybara", "Core Funding", "IMPERIAL", "LENDINI", "LG", "Lifetime Funding","TBF Group", "Flash Advance", "JRG Funding", "Ace Funding", "Slate", "Ark Capital", "Merchant Marketplace", "Specialty Capital", "MERK FUNDING", "MR ADVANCE", "PEARL", "Barnard Fifth", "Queen Funding", "TYCOON", "BlueSky", "CFG", "Knightbridge", "LEND BUG", "Liquidibee", "MANTIS", "Apex Funding", "Zahav Asset Management", "Bow Apple Capital", "BITTY", "Unlimited", "Meged Funding", "Vault Capital LLC", "LCF Group", "AJ EQUITY", "Wynwood", "Yns funding", "Fratello Capital", "GFE", "Global Funding Experts", "QFS Capital", "SILVERLINE", "Throttle Funding", "Lendora", "2m7", "E Advance", "BlueVine", "RIVER ADVANCE", "TVT Capital", "World Business Lenders", "ARF FINANCIAL", "CREDIBLY","ARVI FUND","AVION FD","CHECKCARD","Bridge Fun","EPIC ADVANC","Fundbox INC","ONDECK CAPITAL","Pinnacle Busines","SLATE ADVANCE","Slate Funding","WIRE IN DATE","WIRE OUT DATE","WIRE TYPE","ORANGE ADV","Custom Capital","PARKSIDE FUND","SELECT FUNDING"]

    # Check if description contains any lender's name, case insensitively
    for lender in lenders:
        if lender.lower() in description.lower():
            return "Lender Payment"+","+lender
    keyword_map = {
        "Positive": ["ATM Cash Deposit", "Money Transfer authorized", "WT Fed#", "Credit", "Deposit", "Refund", "Return", "Interest Paid", "Dividend Received", "Bonus Earned", "Rebate", "DES:Corp Pay", "Cash Back", "Rewards Redemption", "Maturity"
                     ],
        "Negative": ["Purchase authorized", "Recurring Payment", "Wire Trans Svc Charge", "Monthly Service Fee", "Direct Pay", "Bill Pay", "Zelle to", "Overdraft", "Paypal Inst Xfer", "ATM Withdrawal", "Debit Card Transaction", "Payment Due", "Fee Assessed", "Service Charge", "Loan Repayment", "Charge", "Late Fee", "Withdrawal Made In A Branch", "Penalty", "Cash eWithdrawal",
                     ],
        "Neutral": ["Internal Transfer", "External Transfer", "Zelle Transfer Conf", "Mobile Transfer", "Online Transfer", "Auto Transfer", "Zelle From", "Wire Transfer"
                    ]
    }
    for transaction_type, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword.lower() in description.lower():
                return transaction_type
    return ""


def extract_details(text: str):
    deposits = []
    withdrawals = []
    transaction_pattern = re.compile(
        r'(\d{2}/\d{2}/\d{4})\s+(.*?)(\$[\d,]+\.\d{2})')
    matches = transaction_pattern.findall(text)

    for match in matches:
        date, description, amount = match
        amount_cleaned = amount.replace(',', '').replace('$', '')
        if description.lower().startswith("yourpreviousbalance"):
            continue  # We ignore these entries
        if "interestpaidthisstatement" in description.lower():
            deposits.append({
                "date": date,
                "description": description,
                "amount": amount_cleaned
            })
        else:
            withdrawals.append({
                "date": date,
                "description": description,
                "amount": amount_cleaned
            })

    return {"deposits": deposits, "withdrawals": withdrawals}
def UploadData(request):
    if request.method == "POST":
        uploaded_file = request.FILES.getlist('upload_files')
        for f in uploaded_file:
            myuploadFile(myfiles=f).save()
        folder_path = 'media'
        all_data = []
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(folder_path, filename)
                pdf_content = extract_text_from_pdf(pdf_path)
                rows = parse_rows(pdf_content)
                all_data.extend(rows)
        lender_payment=0.0
        positive_payment=0.0
        negative_payment=0.0
        neutral_payment=0.0
        date = []
        description = []
        amount = []
        transaction_t = []
        lender = []
        media_folder='media'
        for filename in os.listdir(media_folder):
            file_path = os.path.join(media_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        for row in rows:
            if row[3] == "Positive":
                positive_payment += float(row[2].replace(',', ''))
            if row[3] == "Negative":
                negative_payment += float(row[2].replace(',', ''))
            if row[3] == "Neutral":
                neutral_payment += float(row[2].replace(',', ''))
            explode_data = row[3].split(",")
            if explode_data[0] == "Lender Payment":
                lender_payment += float(row[2].replace(',', ''))
                date.append(row[0]),
                description.append(row[1]),
                amount.append(row[2].replace(',', '')),
                transaction_t.append(explode_data[0]),
                lender.append(explode_data[1]),
            else:
                date.append(row[0]),
                description.append(row[1]),
                amount.append(row[2].replace(',', '')),
                transaction_t.append(row[3]),
                lender.append(""),
        array_data = zip(date, description, amount, transaction_t, lender)
        return render(request, "view-data.html",{"array_data":array_data,"negative_payment":negative_payment,"positive_payment":positive_payment,"neutral_payment":neutral_payment})
    else:
        return render(request, 'upload-pdf.html')
if __name__ == "__main__":
    UploadData()
