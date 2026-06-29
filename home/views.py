import os
import re
import shutil
from cloudinary.uploader import upload as cloudinary_upload
from django.db import IntegrityError
import cloudinary
import boto3
from botocore.config import Config
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from s3transfer import TransferConfig
from django.db.models import Value
from zipfile import ZipFile, ZIP_DEFLATED
import urllib.request
from datetime import datetime
from home.models import *
from django.views.decorators.csrf import csrf_exempt
import uuid
import json
import requests
from num2words import num2words
from django.conf import settings
from odf.opendocument import load
from odf.text import P, Span
from odf.element import Element
from odf.table import Table, TableRow, TableCell
from django.core.mail import EmailMessage
from dotenv import load_dotenv
from django.forms.models import model_to_dict
import hashlib
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from .tasks import delete_user_uploads
from .ccavenue_utils import encrypt, decrypt
import urllib.parse
from datetime import timedelta
from django.utils import timezone

@login_required
def upload_document(request):
    if request.method == "POST":

        # 🔥 delete old files in background
        delete_user_uploads.delay(request.user.id)

        # then save new files
        file = request.FILES.get('file')

        documents.objects.create(
            user=request.user,
            file_location=file
        )

        return redirect('profile')

load_dotenv(dotenv_path='./.env')
import random

def terms(request):
    return render(request, 'policies/terms.html')

def privacy(request):
    return render(request, 'policies/privacy.html')

def cancellation(request):
    return render(request, 'policies/cancellation.html')

def refund(request):
    return render(request, 'policies/refund.html')

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if name and email and subject and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            return JsonResponse({
                "success": True,
                "message": "Your message has been sent successfully!"
            })

        return JsonResponse({
            "success": False,
            "message": "Please fill all fields."
        })

    return JsonResponse({"success": False})

def generate_otp():
    return str(random.randint(100000, 999999))

# x_api_version = '2023-08-01'
# CASHFREE_APP_ID = os.getenv('CASHFREE_APP_ID')
# CASHFREE_SECRET_KEY = os.getenv('CASHFREE_SECRET_KEY')
# CASHFREE_API_URL = os.getenv('CASHFREE_API_URL')

# PAYU_MERCHANT_KEY = os.getenv('PAYU_MERCHANT_KEY')
# PAYU_MERCHANT_SALT = os.getenv('PAYU_MERCHANT_SALT')
# PAYU_BASE_URL = os.getenv('PAYU_BASE_URL')
CCAVENUE_MERCHANT_ID = os.getenv("CCAVENUE_MERCHANT_ID")
CCAVENUE_WORKING_KEY = os.getenv("CCAVENUE_WORKING_KEY")
CCAVENUE_ACCESS_CODE = os.getenv("CCAVENUE_ACCESS_CODE")

# Test URL
CCAVENUE_URL = os.getenv("CCAVENUE_URL")

def home_view(request):
    if request.user.is_anonymous:
        template = "index.html"
        course_type = request.GET.get("course_type", "DevOps") 
         
        try:
            course_list = course.objects.filter(course_type=course_type).order_by("id")  
        except Exception as e:
            return JsonResponse({"status": "error", "Message": f"Course details not found - {str(e)}"}, status=400)
        context = {"course_list": course_list}
        
        return render(request, template, context)
    else:
        return redirect(profile_view)
    
def course_by_id(request, course_id):
    try:
        package = course.objects.get(id=course_id)
        return JsonResponse({"status":"success", "course_duration":package.duration,"course_concept":package.course_concept,
                             "course_eligibility":package.course_eligibility,"course_format":package.course_format, 
                             "course_slogan":package.course_slogan,"course_id":package.id,"course_img":package.image.url,
                             "course_title":package.title,"course_price":package.price,"course_description":package.description})
    except Exception as e:
        return JsonResponse({"status":"error","Message":f"Course details not found - {str(e)}"}, status=400)

def course_by_type(request, course_type):
    try:
        packages = course.objects.filter(course_type=course_type)
        template = "index_consultancy.html"
        return render(request, template, {'course_list': packages})
    except Exception as e:
        return JsonResponse({"status":"error","Message":f"Course details not found - {str(e)}"}, status=400)

@login_required(login_url='/login/')
def change_password(request):
    return render(request, "password_change.html")

@csrf_exempt
@login_required(login_url='/login/')
def change_password_submit(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('new_password1')
        if not new_password or new_password != confirm_password:
            return JsonResponse({"status": "error", "message": "Passwords do not match or are empty"})
        user = request.user
        user.set_password(new_password)
        user.save()
        return JsonResponse({"status":"success", "message":"Changed password Successfully", "data": {
                "username": user.username,
                "email": user.email,
                "id": user.id
            }
        })
    return JsonResponse({"status": "error", "message": "Invalid request method"})

# @login_required(login_url='/login/')
# @csrf_exempt
# def create_order(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Invalid request"}, status=405)

#     try:
#         data = json.loads(request.body)
#         course_id = data.get("courseId")
#         package = get_object_or_404(course, id=course_id)

#         txnid = str(uuid.uuid4())[:20]

#         amount = str(package.price)
#         productinfo = package.title
#         firstname = request.user.first_name
#         email = request.user.email
#         phone = str(profile.objects.get(user=request.user).phone_number)

#         # 🔐 Generate Hash
#         hash_string = f"{PAYU_MERCHANT_KEY}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{PAYU_MERCHANT_SALT}"
#         hashh = hashlib.sha512(hash_string.encode()).hexdigest()

#         # Save payment
#         Payment.objects.create(
#             course_id=package,
#             userid=request.user,
#             order_id=txnid,
#             amount=amount,
#             paid=False
#         )

#         return JsonResponse({
#             "txnid": txnid,
#             "amount": amount,
#             "productinfo": productinfo,
#             "firstname": firstname,
#             "email": email,
#             "phone": phone,
#             "hash": hashh,
#             "key": PAYU_MERCHANT_KEY,
#             "url": PAYU_BASE_URL,
#             "surl": "http://127.0.0.1:8000/payment-success/",
#             "furl": "http://127.0.0.1:8000/payment-failure/"
#         })

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def send_guest_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    data = json.loads(request.body)
    email = data.get("email")

    if not email:
        return JsonResponse({"error": "Email required"}, status=400)

    otp = str(random.randint(100000, 999999))

    LoginOTP.objects.create(
        email=email,
        otp=otp,
        purpose="email_verification"
    )

    send_mail(
        subject="Your OTP for Tekbind Payment",
        message=f"Your OTP is {otp}. Valid for 5 minutes.",
        from_email="tekbind7@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )

    return JsonResponse({"message": "OTP sent successfully"})

@csrf_exempt
def verify_guest_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    data = json.loads(request.body)
    email = data.get("email")
    otp = data.get("otp")

    record = LoginOTP.objects.filter(email=email, otp=otp, purpose="email_verification").last()

    if not record:
        return JsonResponse({"error": "Invalid OTP"}, status=400)

    if record.is_expired():
        return JsonResponse({"error": "OTP expired"}, status=400)

    return JsonResponse({"message": "OTP verified"})
@login_required
@csrf_exempt
def create_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    try:
        data = json.loads(request.body)

        course_id = data.get("courseId")

        if not course_id or str(course_id) == "undefined":
            return JsonResponse({"error": "Invalid course ID"}, status=400)
        user = request.user
        # name = data.get("name")
        # email = data.get("email")
        # phone = data.get("phone")
        # address = data.get("address")

        package = get_object_or_404(course, id=course_id)
        name = user.get_full_name()
        email = user.email
        pro = profile.objects.filter(user=user).first()
        if pro:
            phone = pro.phone_number
            address = pro.present_address
            city = pro.city
            state = pro.state
            zip_code = pro.zip_code
            country = pro.country
        order_id = str(uuid.uuid4())[:20]
        amount = str(package.price)

        # ✅ Save Payment
        Payment.objects.create(
            course_id=package,
            name=name,
            email=email,
            phone=phone,
            address=address,
            order_id=order_id,
            amount=amount,
            paid=False
        )
        print("WORKING KEY:", CCAVENUE_WORKING_KEY)
        print({
            "profile":pro,
            "billing_name": name,
            "billing_email": email,
            "billing_tel": phone,
            "billing_address": address,
            "billing_city": city,
            "billing_state": state,
            "billing_country": country,
            "billing_zip": zip_code,
        })
        if not CCAVENUE_WORKING_KEY:
            return JsonResponse({"error": "Working key missing in settings"})
        base_url = request.build_absolute_uri('/')[:-1]
        merchant_data = {
            "merchant_id": CCAVENUE_MERCHANT_ID,
            "order_id": order_id,
            "currency": "INR",
            "amount": amount,
            "redirect_url": f"{base_url}/payment-success/",
            "cancel_url": f"{base_url}/payment-failure/",
            "billing_name": name,
            "billing_email": email,
            "billing_tel": phone,
            "billing_address": address,
            "billing_city": city,
            "billing_state": state,
            "billing_country": country,
            "billing_zip": zip_code,
        }

        # Convert dict → query string
        merchant_str = urllib.parse.urlencode(merchant_data)

        # 🔐 Encrypt
        encrypted_data = encrypt(merchant_str, CCAVENUE_WORKING_KEY)

        return JsonResponse({
            "encRequest": encrypted_data,
            "access_code": CCAVENUE_ACCESS_CODE,
            "url": CCAVENUE_URL
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from django.contrib import messages   
@csrf_exempt
def payment_success(request):
    encResp = request.POST.get("encResp")
    if not encResp:
        return redirect("/courses/")
    try:
        decrypted = decrypt(encResp, CCAVENUE_WORKING_KEY)
        data = dict(
            item.split("=", 1)
            for item in decrypted.split("&")
            if "=" in item
        )
        print("CCAVENUE RESPONSE:", data)
        order_id = data.get("order_id")
        order_status = data.get("order_status")
        payment = Payment.objects.get(order_id=order_id)
        if order_status and order_status.lower() == "success":
            payment.paid = True
            payment.payment_id = data.get("tracking_id")
            payment.save()
            # Generate invoice
            response = invoice_generate(
                request,
                payment.course_id.id
            )
            print("Invoice Response:", response.content)
            invoice_url = None
            if response.status_code == 200:
                invoice_data = json.loads(
                    response.content.decode("utf-8")
                )
                invoice_url = invoice_data.get("invoice_link")
                print("Invoice URL:", invoice_url)
                if invoice_url:
                    payment.invoice_link = invoice_url
                    payment.save()
                    # Send Email
                    send_invoice_email(
                        payment,
                        invoice_url
                    )
                    # Redirect with invoice URL
                    return redirect(
                        f"/courses/?invoice_url={urllib.parse.quote(invoice_url)}"
                    )
            return redirect("/courses/")
        else:
            payment.paid = False
            payment.save()
            return redirect("/payment-failure/")
    except Exception as e:
        print("PAYMENT SUCCESS ERROR:", str(e))
        return redirect("/courses/")
    
@csrf_exempt
def payment_failure(request):
    return HttpResponse("Payment Failed")

def register_view(request, group_id, message=''):
    template = "register.html"
    selected_group = CourseGroup.objects.filter(id=group_id, status='active').first()
    if not selected_group:
        return redirect('/')
    context = {"message": message, "selected_group":selected_group}
    return render(request, template, context)


def login_view(request, message=''):
    template = "login.html"
    context = {"message": message}
    return render(request, template, context)

def courses(request, paymnet_status=None):
    course_type = request.GET.get("course_type", "DevOps") 
    invoice_url = request.session.pop('invoice_url', None) 
    try:
        course_list = course.objects.filter(course_type=course_type).order_by("id")
    except Exception as e:
        return JsonResponse({"status": "error", "Message": f"Course details not found - {str(e)}"}, status=400)
    
    return render(request, 'courses.html', {
        'course_list': course_list,
        'invoice_url':invoice_url,
        "is_authenticated": request.user.is_authenticated
    })

from PyPDF2 import PdfReader, PdfWriter
def copy_pdf(source_path, destination_path):
    source_pdf = PdfReader(source_path)
    pdf_writer = PdfWriter()
    for page_num in range(len(source_pdf.pages)):
        page = source_pdf.pages[page_num]
        pdf_writer.add_page(page)
    with open(destination_path, "wb") as output_pdf:
        pdf_writer.write(output_pdf)
    
import subprocess
import uno
def replace_text_in_paragraph(paragraph, search_text, replace_text):
    for span in paragraph.getElementsByType(Span):
        if span.firstChild:  
            if hasattr(span.firstChild, 'data'):
                text_content = span.firstChild.data
            elif hasattr(span.firstChild, 'textContent'):
                text_content = span.firstChild.textContent
            else:
                continue  
            text_content = text_content.replace("\n", "").strip()
            if search_text in text_content:
                replaced_text = text_content.replace(search_text, replace_text)
                if hasattr(span.firstChild, 'data'):
                    span.firstChild.data = replaced_text
                elif hasattr(span.firstChild, 'textContent'):
                    span.firstChild.textContent = replaced_text
                    
def replace_text_in_table(table, label_code, label_value):
    for row in table.getElementsByType(TableRow):
        for cell in row.getElementsByType(TableCell):
            paragraphs = cell.getElementsByType(P)
            for para in paragraphs:
                replace_text_in_paragraph(para, label_code, label_value)
                
def convert_pdf_to_docx_using_unoconv(template_local):
    proccessed_pdf = template_local.replace('.pdf', '.odt')
    try:
        subprocess.run(['unoconv', '-f', 'odt', template_local], check=True)
        return proccessed_pdf
    except Exception as e:
        return None  
    
def convert_docx_to_pdf_using_unoconv(proccessed_pdf):
    saved_pdf = proccessed_pdf.replace('.odt', '.pdf')
    try:
        subprocess.run(['unoconv', '-f', 'pdf', proccessed_pdf], check=True)
        return saved_pdf
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None
    
def invoice_generate(request, course_id):
    file_path = os.path.join("static/invoice", "Invoice Template.pdf")

    local_pdf = None
    odt_path = None
    final_pdf_path = None

    try:
        course_detail = get_object_or_404(course, id=course_id)

        order = Payment.objects.filter(course_id=course_detail, paid=True).order_by('-date').first()
        if not order:
            return JsonResponse({"error": "No successful payment found"}, status=404)

        # ✅ GUEST DATA ONLY
        name = order.name or ''
        email = order.email or ''
        phone = order.phone or ''
        address = order.address or ''

        date_today = datetime.today().date()
        course_price = float(course_detail.price or 0)

        course_cost = round(course_price / 1.18, 2)
        cgst = round(course_cost * 0.09, 2)
        sgst = round(course_cost * 0.09, 2)

        data = {
            '<date>': str(date_today),
            '<name>': name,
            '<address>': address,
            '<email>': email,
            '<phone>': phone,
            '<course_name>': course_detail.title or '',
            '<cou_price>': str(course_price),
            '<course_cost>': str(course_cost),
            '<cgst_cost>': str(cgst),
            '<sgst_cost>': str(sgst),
            '<price_words>': num2words(course_price),
        }

        output_dir = os.path.join(settings.MEDIA_ROOT, 'generated_invoice')
        os.makedirs(output_dir, exist_ok=True)

        filename = f"Invoice_{order.order_id}_{order.date.strftime('%Y%m%d')}.pdf"
        local_pdf = os.path.join(output_dir, filename)

        copy_pdf(file_path, local_pdf)

        # Convert PDF → ODT
        odt_path = convert_pdf_to_docx_using_unoconv(local_pdf)
        if not odt_path:
            return JsonResponse({'error': 'PDF to ODT failed'}, status=500)

        odt_doc = load(odt_path)

        for para in odt_doc.getElementsByType(P):
            for k, v in data.items():
                if v:
                    replace_text_in_paragraph(para, k, str(v))

        for table in odt_doc.getElementsByType(Table):
            for k, v in data.items():
                if v:
                    replace_text_in_table(table, k, str(v))

        odt_doc.save(odt_path)

        # Convert ODT → PDF
        final_pdf_path = convert_docx_to_pdf_using_unoconv(odt_path)
        if not final_pdf_path:
            return JsonResponse({'error': 'ODT to PDF failed'}, status=500)

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            final_pdf_path,
            resource_type="raw",
            upload_preset="public_pdf",
            public_id=f"invoices/invoice_{order.order_id}",
            use_filename=True,
            unique_filename=False
        )

        invoice_url = upload_result["secure_url"]

        order.invoice_link = invoice_url
        order.save()

        return JsonResponse({
            "message": "Invoice generated",
            "invoice_link": invoice_url
        })

    except Exception as e:
        import traceback
        print("FULL ERROR:\n", traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)

    finally:
        for path in [local_pdf, odt_path, final_pdf_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_error:
                    print("Cleanup error:", cleanup_error)
    
import tempfile
def send_invoice_email(order, invoice_url):
    try:
        name = order.name
        email = order.email

        if not email:
            return

        # 📥 Download invoice
        response = requests.get(invoice_url)
        response.raise_for_status()

        temp_file_path = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        # 📧 Email config
        subject = "Tekbind Course Invoice"
        from_email = "tekbind7@gmail.com"
        to = [email]
        cc = ["tekbindinvoice@gmail.com", "devops6868@gmail.com"]

        html_content = f"""
        <p>Dear <strong>{name}</strong>,</p>

        <p>Thank you for purchasing the course.</p>

        <p>Please find your invoice attached.</p>

        <p>Contact us: <strong>+91 96636 54114</strong></p>

        <p>Regards,<br><strong>Tekbind Team</strong></p>
        """

        msg = EmailMessage(subject, html_content, from_email, to, cc=cc)
        msg.content_subtype = "html"
        msg.attach_file(temp_file_path)
        msg.send()

    except Exception as e:
        print("Email error:", str(e))

    finally:
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

@csrf_exempt
def emailInvoice(request):
    if request.method == "POST":
        data = json.loads(request.body)
        invoice_url = data.get("invoice_url")
        order_id = data.get("order_id")  
        if not invoice_url or not order_id:
            return JsonResponse({"error": "Missing invoice_url or order_id"}, status=400)
        temp_file_path = None
        try:
            # ✅ Get payment record
            order = Payment.objects.filter(order_id=order_id, paid=True).first()
            if not order:
                return JsonResponse({"error": "Valid payment not found"}, status=404)

            # ✅ Handle BOTH user types
            if order.userid:
                name = order.userid.first_name
                email = order.userid.email
            else:
                name = order.name
                email = order.email

            # 📥 Download invoice
            response = requests.get(invoice_url)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            # 📧 Email config
            subject = 'Tekbind Course Invoice'
            from_email = 'tekbind7@gmail.com'
            to = [email]
            cc_recipients = ['tekbindinvoice@gmail.com', 'devops6868@gmail.com', 'tekbindservices@gmail.com']

            html_content = f"""
            <p>Dear <strong>{name}</strong>,</p>

            <p>Thank you for successfully purchasing the course.</p>

            <p>Please find your invoice attached for your records.</p>

            <p>If you have any questions, contact us at <strong>+91 96636 54114</strong>.</p>

            <p>Best regards,</p>
            <p><strong>Tekbind Team</strong></p>
            """

            msg = EmailMessage(subject, html_content, from_email, to, cc=cc_recipients)
            msg.content_subtype = "html"
            msg.attach_file(temp_file_path)
            msg.send()

            return JsonResponse({"message": "Invoice email sent successfully"})

        except requests.RequestException as e:
            return JsonResponse({"error": f"Download failed: {str(e)}"}, status=500)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as cleanup_error:
                    print(f"Cleanup failed: {cleanup_error}")

def create_course_group(request):
    if request.method == "POST":
        name = request.POST.get("group_name")
        description = request.POST.get("description")
        status = request.POST.get("status")

        CourseGroup.objects.create(
            name=name,
            description=description,
            status=status
        )

    return redirect("/profile/")

@login_required(login_url='/login/')
def assign_candidates_group(request):

    if request.method == "POST":

        group_id = request.POST.get("group_id")

        candidate_ids = request.POST.getlist("candidates")

        selected_group = CourseGroup.objects.filter(
            id=group_id
        ).first()

        profile.objects.filter(
            user_id__in=candidate_ids
        ).update(
            course_group=selected_group
        )

    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='/login/')
def assign_admins_group(request):

    if request.method == "POST":

        group_id = request.POST.get("group_id")

        admin_ids = request.POST.getlist("admins")

        selected_group = CourseGroup.objects.filter(
            id=group_id
        ).first()

        if selected_group:

            # clear previous admins if needed
            selected_group.admin_course_group.clear()

            # add selected admins
            for admin_id in admin_ids:

                try:
                    admin_user = User.objects.get(
                        id=admin_id,
                        is_staff=True
                    )

                    selected_group.admin_course_group.add(
                        admin_user
                    )

                except:
                    pass

    return redirect(
        request.META.get('HTTP_REFERER')
    )

@login_required(login_url='/login/')
def toggle_course_group_status(request):

    if request.method == "POST":

        group_id = request.POST.get("group_id")

        group = CourseGroup.objects.filter(
            id=group_id
        ).first()

        if group:

            if group.status == "active":
                group.status = "inactive"
            else:
                group.status = "active"

            group.save()

    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='/login/')
def profile_view(request, user_id=None):
    template = "profile.html"

    # 🔍 SEARCH HANDLING
    search_candidate = request.POST.get('search_candidate')
    user_id_from_form = request.POST.get('user_id')

    if user_id_from_form:
        user_id = user_id_from_form

    elif search_candidate:
        try:
            search_candidate_id = search_candidate.split('-')[-1]
            if request.user.is_superuser and request.user.is_staff:
                user_id = profile.objects.select_related('user').get(
                    id=search_candidate_id
                ).user.id
            elif request.user.is_staff and not request.user.is_superuser:
                admin_groups = CourseGroup.objects.filter( admin_course_group=request.user )
                selected_candidate = profile.objects.select_related( 'user' ).get( id=search_candidate_id, course_group__in=admin_groups )
                user_id = selected_candidate.user.id
            else:
                user_id=request.user.id

        except:
            user_id = request.user.id

    # 🔒 ACCESS CONTROL
    if not user_id or not (
        request.user.is_staff or request.user.is_superuser
    ):
        user_id = request.user.id

    # ✅ PROFILE
    data = profile.objects.select_related(
        'user',
        'course_group'
    ).filter(user_id=user_id).first()

    # ✅ EDUCATION
    educations = education.objects.filter(user_id=user_id)
    edu_map = {e.course_level: e for e in educations}

    # ✅ EXPERIENCE
    exp = experience.objects.filter(user_id=user_id)

    # ✅ DOCUMENTS
    docs_qs = documents.objects.filter(user_id=user_id).only(
        'file_location',
        'file_title'
    )

    docs_map = {}

    for d in docs_qs:
        file_obj = d.file_location
        file_download_url = None

        if (
            file_obj and
            hasattr(file_obj, 'url') and
            'upload' in file_obj.url
        ):
            url_part = file_obj.url.split('upload', 1)

            file_download_url = (
                f"{url_part[0]}upload/fl_attachment"
                f"{url_part[1]}"
            )

        docs_map[d.file_title] = {
            'file': file_obj,
            'download_url': file_download_url
        }

    # ✅ ALL CANDIDATES
    candidates = profile.objects.filter(
        user__is_superuser=False,
        user__is_staff=False
    ).values(
        'id',
        'course_group_id',
        'user__id',
        'user__first_name',
        'user__last_name'
    )

    # ✅ ADMINS
    admins = User.objects.filter(
        is_staff=True,
        is_superuser=False
    ).only(
        'id',
        'first_name',
        'last_name'
    )
    # # ✅ ALL USERS (OPTIMIZED)

    # if request.user.is_superuser and request.user.is_staff:

    #     all_users = profile.objects.select_related('user').filter(
    #         user__is_superuser=False,
    #         user__is_staff=False
    #     ).only(
    #         'id',
    #         'course_group_id',
    #         'user__id',
    #         'user__first_name',
    #         'user__last_name'
    #     )

    # elif request.user.is_staff and not request.user.is_superuser:

    #     # get admin assigned group ids only
    #     admin_group_ids = CourseGroup.objects.filter(
    #         admin_course_group=request.user
    #     ).values_list('id', flat=True)

    #     # filter only candidates from those groups
    #     all_users = profile.objects.select_related('user').filter(
    #         course_group_id__in=admin_group_ids,
    #         user__is_superuser=False,
    #         user__is_staff=False
    #     ).only(
    #         'id',
    #         'course_group_id',
    #         'user__id',
    #         'user__first_name',
    #         'user__last_name'
    #     )

    # else:
    #     all_users = profile.objects.none()

    # ✅ COURSE GROUPS
    course_groups = CourseGroup.objects.only(
        'id',
        'name',
        'description',
        'status'
    )
    my_courses = Payment.objects.filter(
        email=request.user.email,
        paid=True
    ).select_related("course_id").order_by("-id")
    from django.db.models import Sum
    from django.core.paginator import Paginator
    total_spent = my_courses.aggregate(total=Sum("amount"))["total"] or 0
    all_course_purchases = Payment.objects.select_related('course_id').order_by('-date')
    # Pagination
    paginator = Paginator(all_course_purchases, 10)  # 20 records per page
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    # Revenue
    total_revenue = Payment.objects.filter(paid=True).aggregate(total=Sum('amount'))['total'] or 0
    context = {
        'data': data,
        'master': edu_map.get('master'),
        'degree': edu_map.get('degree'),
        'plus_two_diploma': edu_map.get('plus_two_diploma'),
        'sslc': edu_map.get('sslc'),
        'documents': docs_map,
        'experience_list': exp,
        # 'all_users': all_users,
        'course_groups': course_groups,
        # ✅ NEW
        'candidates': candidates,
        'admins': admins,
        'my_courses':my_courses,
        "total_spent": total_spent,
        "transactions":transactions,
        "total_revenue": total_revenue,
    }
    return render(request, template, context)

@login_required(login_url='/login/')
def deassign_candidate_group(request):

    if request.method == "POST":

        candidate_id = request.POST.get("candidate_id")

        try:
            candidate = profile.objects.get(id=candidate_id)

            candidate.course_group = None
            candidate.save()

            messages.success(
                request,
                "Candidate removed from group successfully."
            )

        except profile.DoesNotExist:
            messages.error(
                request,
                "Candidate not found."
            )

    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/login/')
def candidate_search_api(request):

    search = request.GET.get('q', '').strip()

    queryset = profile.objects.select_related('user')

    # SUPERADMIN
    if request.user.is_superuser and request.user.is_staff:

        queryset = queryset.filter(
            user__is_superuser=False,
            user__is_staff=False
        )

    # ADMIN
    elif request.user.is_staff and not request.user.is_superuser:

        admin_group_ids = CourseGroup.objects.filter(
            admin_course_group=request.user
        ).values_list('id', flat=True)

        queryset = queryset.filter(
            course_group_id__in=admin_group_ids,
            user__is_superuser=False,
            user__is_staff=False
        )

    else:
        return JsonResponse([], safe=False)

    # SEARCH FILTER
    queryset = queryset.filter(
        user__first_name__icontains=search
    )

    data = []

    for item in queryset:
        data.append({
            "id": item.id,
            "name": f"{item.user.first_name} {item.user.last_name}"
        })

    return JsonResponse(data, safe=False)

@csrf_exempt
def register_api(request, group_id=None, key="CREATE", user_id=None):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    # -------------------------
    # INPUTS
    # -------------------------
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')

    phone_number = request.POST.get('phone_number', "")
    whatsapp_number = request.POST.get('whatsapp_number', "")
    dob = request.POST.get('dob', "")
    father = request.POST.get('father', "")
    mother = request.POST.get('mother', "")
    aadhar = request.POST.get('aadhar', "")
    pan = request.POST.get('pan', "")
    pan_name = request.POST.get('pan_name', "")
    passport = request.POST.get('passport', "")
    marital = request.POST.get('marital', "")
    gender = request.POST.get('gender', "")
    blood = request.POST.get('blood', "")
    batch = request.POST.get('batch', "")
    batch_month = request.POST.get('batch_month', "")
    batch_timings = request.POST.get('batch_timings', "")
    batch_year = request.POST.get('batch_year', "")
    reference = request.POST.get('reference', "")
    interests = request.POST.get('interests', "")
    skill_set = request.POST.get('skill_set', "")
    about = request.POST.get('about', "")
    present_address = request.POST.get('present_address', "")
    permanent_address = request.POST.get('permanent_address', "")
    profile_status = request.POST.get('profile_status', "")
    city = request.POST.get('city',"")
    state = request.POST.get('state',"")
    country = request.POST.get('country',"")
    zip_code = request.POST.get('zip_code',"")
    uan = request.POST.get('uan', "")

    # -------------------------
    # GET USER SAFELY
    # -------------------------
    user = None

    if email:
        user = User.objects.filter(username=email).first()
    elif request.user.is_authenticated:
        user = request.user
        email = request.user.email

    # -------------------------
    # CREATE FLOW
    # -------------------------
    if key == "CREATE":
        if user:
            return JsonResponse({"error": "User already exists"}, status=400)
        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "Email already exists"}, status=400)
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            selected_group = CourseGroup.objects.filter(
                id=group_id,
                status='active'
            ).first()
            
            if selected_group:
                user.profile.course_group = selected_group
                user.profile.save()
        except Exception as e:
            return JsonResponse({"error": f"User creation failed: {str(e)}"}, status=500)

        login(request, user)
        key = "UPDATE"

    # -------------------------
    # UPDATE FLOW
    # -------------------------
    if key == "UPDATE":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        if not user:
            return JsonResponse({"error": "User not found"}, status=404)
        if not user_id:
            user_id = request.user.id
        if int(user_id) != request.user.id and not request.user.is_superuser:
            return JsonResponse({"error": "Permission denied"}, status=403)
        try:
            current_user = User.objects.get(id=user_id)
            current_profile = profile.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except profile.DoesNotExist:
            return JsonResponse({"error": "Profile not found"}, status=404)

        # -------------------------
        # UPDATE USER FIELDS
        # -------------------------
        if email:
            if User.objects.filter(username=email).exclude(id=current_user.id).exists():
                return JsonResponse({"error": "Email already in use"}, status=400)
            current_user.username = email
            current_user.email = email
        if first_name:
            current_user.first_name = first_name
        if last_name:
            current_user.last_name = last_name
        try:
            current_user.save()
        except IntegrityError:
            return JsonResponse({"error": "Duplicate email detected"}, status=400)

        # -------------------------
        # UPDATE PROFILE
        # -------------------------
        update_fields = {
            "phone_number": phone_number,
            "whatsapp_number": whatsapp_number,
            "dob": dob,
            "father": father,
            "mother": mother,
            "aadhar": aadhar,
            "pan": pan,
            "passport": passport,
            "marital": marital,
            "gender": gender,
            "blood": blood,
            "batch": batch,
            "batch_month": batch_month,
            "batch_timings": batch_timings,
            "batch_year": batch_year,
            "present_address": present_address,
            "permanent_address": permanent_address,
            "reference": reference,
            "interests": interests,
            "skill_set": skill_set,
            "about": about,
            "pan_name": pan_name,
            "profile_status": profile_status,
            "uan": uan,
            "city":city,
            "state":state,
            "country":country,
            "zip_code":zip_code
        }
        for field, value in update_fields.items():
            if value:
                setattr(current_profile, field, value)
        current_profile.save()
    return redirect('profile_view', user_id or request.user.id)

def login_api(request):
    email = request.POST.get('email', '')
    password = request.POST.get('password', '')

    try:
        user_obj = User.objects.get(email=email)
        user = authenticate(username=user_obj.username, password=password)

        if not user:
            return JsonResponse(
                {"error": "Invalid credentials"},
                status=401
            )
        # trusted_token = request.COOKIES.get("trusted_device")
        # if trusted_token:
        #     trusted_device = TrustedDevice.objects.filter(
        #         user=user,
        #         token=trusted_token,
        #         expires_at__gt=timezone.now()
        #     ).first()
        # if trusted_device:
        #     login(request, user)
        #     return JsonResponse({
        #         "status": "success",
        #         "message": "Trusted device login",
        #         "user_id": user.id
        #     })

        # ✅ NORMAL USER → DIRECT LOGIN (NO OTP)
        if not user.is_staff and not user.is_superuser:
            login(request, user)
            return JsonResponse({
                "status": "success",
                "user_id": user.id
            })

        # Delete old OTPs
        LoginOTP.objects.filter(user=user).delete()

        # Generate OTP
        otp = generate_otp()

        # Save OTP
        # LoginOTP.objects.create(user=user, otp=otp)
        otp_obj = LoginOTP(user=user, email=user.email, purpose="login")
        otp_obj.set_otp(otp)
        otp_obj.save()

        # Decide receiver
        # if user.is_superuser:
        #     receiver_email = user.email
        # else:
        #     superuser = User.objects.filter(is_superuser=True).first()
        #     if not superuser:
        #         return JsonResponse({"error": "Superuser not found"}, status=500)
        #     receiver_email = superuser.email

        # Send OTP
        EmailMessage(
            subject="OTP - Tekbind Login Code",
            body = f"Your OTP is {otp} for staff user login. Valid for 5 minutes." if user.is_staff else f"Your OTP is {otp} for super admin login. Valid for 5 minutes.",
            from_email="tekbind7@gmail.com",
            to=["tekbind7@gmail.com"]
        ).send()

        # Store session
        request.session['pre_auth_user_id'] = user.id
        request.session.save()

        return JsonResponse({
            "status": "otp_required",
            "message": f"OTP sent to super admin"
        })

    except User.DoesNotExist:
        return login_view(request, "Invalid Credentials!!")
    
@csrf_exempt
def verify_login_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    otp_input = request.POST.get("otp")
    user_id = request.session.get('pre_auth_user_id')
    if not user_id:
        return JsonResponse({"error": "Session expired"}, status=400)
    try:
        otp_obj = LoginOTP.objects.filter(user_id=user_id).latest('created_at')
    except LoginOTP.DoesNotExist:
        return JsonResponse({"error": "OTP not found"}, status=404)
    if otp_obj.is_expired():
        return JsonResponse({"error": "OTP expired"}, status=400)
    if not otp_obj.check_otp(otp_input):
        return JsonResponse({"error": "Invalid OTP"}, status=400)

    # Login user after verification
    user = User.objects.get(id=user_id)
    login(request, user)

    # Cleanup
    otp_obj.delete()
    request.session.pop('pre_auth_user_id', None)

    return JsonResponse({
        "status": "success",
        "message": "Login successful"
    })

def forgot_password(request):
    return render(request, "forgot_password.html")

@csrf_exempt
def forgot_password_api(request):
    if request.method != "POST":
        return JsonResponse({"error":"Invalid request"}, status=400)
    email = request.POST.get("email","").strip()
    if not email:
        return JsonResponse({"error":"Email required"})
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({"error":"Email not registered"})
    LoginOTP.objects.filter(
        email=email,
        purpose="password_reset"
    ).delete()
    otp = generate_otp()
    otp_obj = LoginOTP(user=user, email=email, purpose="password_reset")
    otp_obj.set_otp(otp)
    otp_obj.save()
    EmailMessage(subject="Tekbind Password Reset OTP",
        body=f"""
            Hello {user.first_name},
                Your OTP for password reset is {otp}
                This OTP is valid for 5 minutes.
            Regards
            Tekbind Team
        """,
        from_email="tekbind7@gmail.com",
        to=[email]
    ).send()
    request.session["reset_email"] = email
    return JsonResponse({
        "status":"success",
        "message":"OTP sent"
    })

@csrf_exempt
def verify_forgot_password_otp(request):
    if request.method != "POST":
        return JsonResponse({"error":"Invalid request"})
    email = request.session.get("reset_email")
    otp = request.POST.get("otp","")
    if not email:
        return JsonResponse({"error":"Session expired"})
    try:
        otp_obj = LoginOTP.objects.filter(
            email=email,
            purpose="password_reset"
        ).latest("created_at")
    except LoginOTP.DoesNotExist:
        return JsonResponse({"error":"OTP not found"})
    if otp_obj.is_expired():
        otp_obj.delete()
        return JsonResponse({"error":"OTP expired"})
    if not otp_obj.check_otp(otp):
        return JsonResponse({"error":"Invalid OTP"})
    otp_obj.is_verified = True
    otp_obj.save()
    return JsonResponse({
        "status":"success"
    })

@csrf_exempt
def resend_forgot_password_otp(request):
    email = request.session.get("reset_email")
    if not email:
        return JsonResponse({"error":"Session expired"})
    otp_obj = LoginOTP.objects.filter(
        email=email,
        purpose="password_reset"
    ).latest("created_at")
    if otp_obj.resend_count >= 3:
        return JsonResponse({
            "error":"Maximum resend limit reached"
        })
    otp = generate_otp()
    otp_obj.set_otp(otp)
    otp_obj.created_at = timezone.now()
    otp_obj.resend_count += 1
    otp_obj.save()
    EmailMessage(
        subject="Password Reset OTP",
        body=f"Your OTP is {otp}",
        from_email="tekbind7@gmail.com",
        to=[email]
    ).send()
    return JsonResponse({
        "status":"resent",
        "count":otp_obj.resend_count
    })

@csrf_exempt
def reset_password_api(request):
    if request.method != "POST":
        return JsonResponse({"error":"Invalid request"})
    email = request.session.get("reset_email")
    password = request.POST.get("password","")
    confirm = request.POST.get("confirm_password","")
    if not email:
        return JsonResponse({"error":"Session expired"})

    if password != confirm:
        return JsonResponse({"error":"Passwords do not match"})

    try:

        otp_obj = LoginOTP.objects.filter(
            email=email,
            purpose="password_reset",
            is_verified=True
        ).latest("created_at")

    except LoginOTP.DoesNotExist:

        return JsonResponse({
            "error":"OTP verification required"
        })

    user = otp_obj.user

    user.set_password(password)

    user.save()

    otp_obj.delete()

    request.session.pop("reset_email",None)

    return JsonResponse({
        "status":"success",
        "message":"Password changed successfully"
    })

@csrf_exempt
def resend_otp(request):
    user_id = request.session.get("pre_auth_user_id")

    if not user_id:
        return JsonResponse({"error": "Session expired"}, status=400)

    try:
        user = User.objects.get(id=user_id)
        otp_obj = LoginOTP.objects.filter(user=user).latest('created_at')
    except (User.DoesNotExist, LoginOTP.DoesNotExist):
        return JsonResponse({"error": "OTP not found"}, status=404)

    # 🚫 LIMIT CHECK
    if otp_obj.resend_count >= 3:
        return JsonResponse({
            "error": "Maximum resend attempts reached"
        }, status=429)

    # 🔐 Generate new OTP
    otp = generate_otp()

    otp_obj.otp = otp
    otp_obj.resend_count += 1
    otp_obj.created_at = now()  # reset timer
    otp_obj.save()

    # # 🎯 Decide receiver
    # if user.is_superuser:
    #     receiver_email = user.email
    # else:
    #     superuser = User.objects.filter(is_superuser=True).first()
    #     receiver_email = superuser.email

    EmailMessage(
            subject="Resend OTP - Tekbind Resend Login Code",
            body = f"Your OTP is {otp} for staff user login. Valid for 5 minutes." if user.is_staff else f"Your OTP is {otp} for super admin login. Valid for 5 minutes.",
            from_email="tekbind7@gmail.com",
            to=["tekbind7@gmail.com"]
        ).send()

    return JsonResponse({
        "status": "resent",
        "resend_count": otp_obj.resend_count
    })

def update_course_details(request):
    user_id = request.POST.get('user_id')
    course = request.POST.get('course')
    course_level = request.POST.get('course_level')
    specialization = request.POST.get('specialization')
    university = request.POST.get('university')
    college = request.POST.get('college')
    year_in = request.POST.get('year_in')
    year_out = request.POST.get('year_out')
    percentage = request.POST.get('percentage')

    if user_id:
        if int(user_id) != request.user.id and not request.user.is_superuser:
            return HttpResponse("Permission Denied", status=403)
    else:
        user_id = request.user.id

    data_exists = education.objects.filter(user_id=user_id, course_level=course_level)

    if not data_exists.count():
        education(user_id=user_id,
                  course_level=course_level,
                  course=course,
                  specialization=specialization,
                  college=college,
                  university=university,
                  year_in=year_in,
                  year_out=year_out,
                  percentage=percentage).save()
    else:
        data_exists.update(course=course,
                           specialization=specialization,
                           college=college,
                           university=university,
                           year_in=year_in,
                           year_out=year_out,
                           percentage=percentage)
    return redirect('profile_view', user_id)


def update_experience(request):
    user_id = request.POST.get('user_id', None)
    experience_id = request.POST.get('experience_id', None)
    company = request.POST.get('company', None)
    designation = request.POST.get('designation', None)
    domain = request.POST.get('domain', None)
    date_in = request.POST.get('date_in', None)
    date_out = request.POST.get('date_out', None)

    if user_id:
        if int(user_id) != request.user.id and not request.user.is_superuser:
            return HttpResponse("Permission Denied", status=403)
    else:
        user_id = request.user.id

    data_exists = experience.objects.filter(id=experience_id, user_id=user_id)

    if data_exists.count() == 0:
        experience(user_id=user_id,
                   company=company,
                   designation=designation,
                   domain=domain,
                   date_in=date_in,
                   date_out=date_out).save()
    else:
        data_exists.update(company=company,
                           designation=designation,
                           domain=domain,
                           date_in=date_in,
                           date_out=date_out)
    return redirect('profile_view', user_id)


AWS_ACCELERATION = "use_accelerate_endpoint"
SNS = 'sns'
S3 = "s3"
INVALID_BUCKET = "Invalid Bucket Name"
BUCKET = "Bucket"
KEY = "key"
ORDER_ID = "order_id"
CONTENTS = "Contents"
CONTENT = "content"
GET_OBJECT = "get_object"
AWS_REGION_ID = "ap-south-1"
import os
AWS_REGION_ID = os.getenv('AWS_REGION_ID')

AWS_S3_ACCESS_KEY_ID = "AKIAxxxxxxxxxx"
AWS_S3_SECRET_ACCESS_KEY = "qHMxxxxxxxxxxxxxxxxxxxxxxJ"
S3_PUBLIC_URL = os.getenv('s3_PUBLIC_URL')
S3_PUBLIC = os.getenv('S3_PUBLIC')

aws_session = boto3.Session(region_name=AWS_REGION_ID,
                            aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY)
aws_config = Config(s3={AWS_ACCELERATION: True})
aws_s3_resource = aws_session.resource(S3, config=aws_config)
s3_client = aws_session.client(S3)
S3_FOLDER = 'grasptek-pv-bk'


def get_s3_file_name(object_name, bucket=S3_FOLDER):
    response = s3_client.generate_presigned_url(GET_OBJECT,
                                                Params={BUCKET: bucket,
                                                        'Key': object_name},
                                                ExpiresIn=604800)
    return re.search("https.*", response, re.DOTALL)[0]


def upload_file(file, file_title, user_id):
    upload_path = "/".join(["media", "documents", str(user_id)])
    output_file = "/".join([upload_path, file_title + "." + file.name.split('.')[-1]])
    if not os.path.exists(upload_path):
        os.umask(0)
        os.makedirs(upload_path, mode=0o777)
    with open(output_file, 'wb') as f:
        f.write(file.read())

    s3_client.upload_file(output_file, S3_FOLDER, output_file)
    return output_file


@login_required(login_url='/login/')
def upload_file_api(request):
    input_file = request.FILES.get('input_file')
    file_title = request.POST.get('file_title')
    user_id = request.POST.get('user_id')

    if user_id:
        if int(user_id) != request.user.id and not request.user.is_superuser:
            return HttpResponse("Permission Denied", status=403)
    else:
        user_id = request.user.id

    doc_qs = documents.objects.filter(user_id=user_id, file_title=file_title)

    if doc_qs.exists():
        doc = doc_qs.first()
        doc.file_location = input_file
        doc.save()
    else:
        documents.objects.create(
            user_id=user_id,
            file_title=file_title,
            file_location=input_file
        )

    return HttpResponse('success')


def logout_view(request):
    logout(request)
    return redirect(home_view)


def edit_experience(request, experience_id=0):
    if request.user.is_superuser:
        exp = experience.objects.filter(id=experience_id)
    else:
        exp = experience.objects.filter(id=experience_id, user_id=request.user.id)
    exp = exp.first() if exp.exists() else None
    if exp.count():
        exp = exp[0]

    context = {"experience": exp}
    template = "experience.html"
    return render(request, template, context)


@login_required(login_url='/login/')
def delete_experience(request, experience_id=0):
    if request.user.is_superuser:
        exp = experience.objects.filter(id=experience_id)
    else:
        exp = experience.objects.filter(id=experience_id, user_id=request.user.id)
    if not exp.exists():
        return HttpResponse("Not Found or Permission Denied", status=404)
    exp.delete()
    return redirect('profile_view')


@login_required(login_url='/login/')
def download_view(request, user_id=None):
    if user_id:
        if int(user_id) != request.user.id and not request.user.is_superuser:
            return HttpResponse("Permission Denied", status=403)
    else:
        user_id = request.user.id

    data_exists = documents.objects.filter(user_id=user_id)
    usr = User.objects.get(id=user_id)
    usr_name = f"{usr.first_name.replace(' ', '_')}_{usr.last_name.replace(' ', '_')}"

    if data_exists:
        base_path = os.path.join("media", "documents", str(user_id))
        abs_path = os.path.join(os.getcwd(), base_path)

        if not os.path.exists(abs_path):
            os.umask(0)
            os.makedirs(abs_path, mode=0o777)

        zip_path = os.path.join(abs_path, usr_name + ".zip")

        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as myzip:
            for doc in data_exists:
                file_url = doc.file_location.url  
                ext = file_url.split('.')[-1].split('?')[0]  
                filename = f"{doc.file_title}.{ext}"
                file_path = os.path.join(abs_path, filename)

                try:
                    urllib.request.urlretrieve(file_url, file_path)
                    myzip.write(file_path, filename)
                except Exception as e:
                    print(f"Error downloading {file_url}: {e}")

        # Serve the zip file
        with open(zip_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{usr_name}.zip"'
            return response

    return HttpResponse("No documents found.")
