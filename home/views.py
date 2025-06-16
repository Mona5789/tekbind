import os
import re
import shutil
from cloudinary.uploader import upload as cloudinary_upload
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

load_dotenv(dotenv_path='./.env')

x_api_version = '2023-08-01'
CASHFREE_APP_ID = os.getenv('CASHFREE_APP_ID')
CASHFREE_SECRET_KEY = os.getenv('CASHFREE_SECRET_KEY')
CASHFREE_API_URL = os.getenv('CASHFREE_API_URL')


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

def change_password(request):
    return render(request, "password_change.html")

@csrf_exempt
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

@login_required(login_url='/login/')
@csrf_exempt
def create_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)
    try:
        data = json.loads(request.body)
        course_id = data.get("courseId")
        package = get_object_or_404(course, id=course_id)

        customer_id = str(request.user.id) if request.user.is_authenticated else str(uuid.uuid4())
        customer_id = customer_id.zfill(3) if len(customer_id) < 3 else customer_id

        payload = {
            "order_id": f"order_{uuid.uuid4().hex[:10]}",  
            "order_amount": float(package.price),
            "order_currency": "INR",
            "customer_details": {
                "customer_id": customer_id,
                "customer_email": str(request.user.email) if request.user.is_authenticated else "test@example.com",
                "customer_phone": str((profile.objects.get(user=request.user)).phone_number) if request.user.is_authenticated else "9999999999",
                "customer_name": str(request.user.first_name) if request.user.is_authenticated else "Guest User"
            },
            "order_meta": {
                "return_url": "https://www.tekbind.com/courses/"
                # "return_url": "http://127.0.0.1:8000/courses/"
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-client-id": CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET_KEY,
            "x-api-version": "2023-08-01",
        }
    
        print("Sending Request to Cashfree...")
        print("Payload:", json.dumps(payload, indent=4))
        print("Headers:", headers)

        response = requests.post(CASHFREE_API_URL, json=payload, headers=headers)
        
        print("Raw Response:", response.text)
        print("Response Status Code:", response.status_code)

        if response.status_code == 200:
            api_response = response.json()
            print("api_response: ", api_response)
            Payment.objects.create(
                course_id=package,
                userid=request.user,
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                order_id=api_response.get("order_id"),
                payment_id=api_response.get("payment_session_id"),
                amount=float(package.price),
                paid=False
            )
            return JsonResponse({
                "status": api_response.get("order_status"),
                "payment_session_id": api_response.get("payment_session_id"),
                "order_id": api_response.get("order_id"),
                "amount": package.price
            })

        else:
            return JsonResponse({"status": "failure", "error": f"Failed to create order: {response.text}"}, status=500)

    except Exception as e:
        print(f"Error creating order: {e}")
        return JsonResponse({"error": f"Internal Server Error - {e}"}, status=500)

@login_required(login_url='/login/') 
@csrf_exempt
def payment_success(request):
    try:
        response = json.loads(request.body.decode('utf-8'))
        print("Payment success: ", response)
        
        cf_order_id = response.get("order_id")
        
        headers = {
            "x-client-id": CASHFREE_APP_ID,  
            "x-client-secret": CASHFREE_SECRET_KEY,  
            "x-api-version": "2023-08-01",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payment_response = requests.get(f"{CASHFREE_API_URL}/{cf_order_id}/payments", headers=headers)
        
        if payment_response.status_code == 200:
            payment_data = payment_response.json()  # Ensure this is a dict, not a list
            print("Payment API Response:", payment_data)

            if isinstance(payment_data, list) and len(payment_data) > 0:
                payment_status = payment_data[0].get("payment_status")
            elif isinstance(payment_data, dict):
                payment_status = payment_data.get("payment_status")
            else:
                return JsonResponse({"status": "error", "message": "Unexpected response format from Cashfree"}, status=500)

            if payment_status == "SUCCESS":
                payment = Payment.objects.get(order_id=cf_order_id)
                payment.paid = True
                payment.save()
                return JsonResponse({"status": "SUCCESS"})
            elif payment_status in ['CANCELLED', 'PENDING', 'NOT_ATTEMPTED']:
                payment = Payment.objects.get(order_id=cf_order_id)
                payment.paid = False
                payment.save()
                return JsonResponse({"status": payment_status})
            else:
                return JsonResponse({"status": "Payment Failed"}, status=400)
        else:
            return JsonResponse({"status": "failure", "error": "Failed to fetch payment status"}, status=500)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def register_view(request, message=''):
    template = "register.html"
    context = {"message": message}
    return render(request, template, context)


def login_view(request, message=''):
    template = "login.html"
    context = {"message": message}
    return render(request, template, context)

@login_required(login_url='/login/')
def courses(request, paymnet_status=None):
    course_type = request.GET.get("course_type", "DevOps")  
    try:
        course_list = course.objects.filter(course_type=course_type).order_by("id")
    except Exception as e:
        return JsonResponse({"status": "error", "Message": f"Course details not found - {str(e)}"}, status=400)
    
    return render(request, 'courses.html', {
        'course_list': course_list,
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

    try:
        course_detail = get_object_or_404(course, id=course_id)
        user_profile = profile.objects.get(user=request.user)
        order = Payment.objects.filter(course_id=course_detail).order_by('-date').first()

        date_today = datetime.today().date()
        course_price = course_detail.price
        course_cost = round(float(course_price) / 1.18, 2)
        cgst = round(course_cost * 0.09, 2)
        sgst = round(course_cost * 0.09, 2)

        data = {
            '<date>': str(date_today),
            '<name>': request.user.first_name if request.user.is_authenticated else '',
            '<address>': f"{user_profile.present_address}" if user_profile.present_address else '',
            '<email>': request.user.email if request.user.is_authenticated else '',
            '<phone>': user_profile.phone_number if user_profile.phone_number else '',
            '<course_name>': course_detail.title if course_detail.title else '',
            '<cou_price>': str(course_price) if str(course_price) else 0,
            '<course_cost>': str(course_cost) if course_cost else 0,
            '<cgst_cost>': str(cgst) if cgst else 0,
            '<sgst_cost>': str(sgst) if sgst else 0,
            '<price_words>': num2words(course_price) if course_price else '',
        }

        # Generate file paths
        output_dir = os.path.join(settings.MEDIA_ROOT, 'generated_invoice')
        os.makedirs(output_dir, exist_ok=True)

        file_base = os.path.splitext(os.path.basename(file_path))[0]
        filename = f"{file_base}_{order.order_id}_{order.date.strftime('%Y%m%d')}.pdf"
        local_pdf = os.path.join(output_dir, filename)

        # Copy original template
        copy_pdf(file_path, local_pdf)

        # Convert PDF to ODT
        odt_path = convert_pdf_to_docx_using_unoconv(local_pdf)
        if not odt_path:
            return JsonResponse({'status': 'error', 'message': 'Failed to convert PDF to ODT.'}, status=500)

        # Load ODT and replace placeholders
        try:
            odt_doc = load(odt_path)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error loading ODT: {e}'}, status=500)

        for para in odt_doc.getElementsByType(P):
            for k, v in data.items():
                if v:
                    replace_text_in_paragraph(para, k, str(v))

        for table in odt_doc.getElementsByType(Table):
            for k, v in data.items():
                if v:
                    replace_text_in_table(table, k, str(v))

        odt_doc.save(odt_path)

        # Convert updated ODT back to PDF
        final_pdf_path = convert_docx_to_pdf_using_unoconv(odt_path)
        if not final_pdf_path:
            return JsonResponse({'status': 'error', 'message': 'Failed to convert ODT to final PDF.'}, status=500)

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(final_pdf_path, resource_type="raw", upload_preset="public_pdf", public_id=f"invoices/invoice_{order.order_id}_{order.date.strftime('%Y%m%d')}", use_filename=True, unique_filename=False)
        invoice_url = upload_result["secure_url"]
        # Save invoice URL to Payment record
        if order:
            order.invoice_link = invoice_url
            order.save()

        return JsonResponse({
            "message": "Invoice generated successfully.",
            "invoice_link": invoice_url
        })

    except Exception as e:
        print(f"Invoice generation error: {e}")
        return JsonResponse({"message": "Error generating invoice", "error": str(e)}, status=500)
    
    finally:
        for path in [local_pdf, odt_path, final_pdf_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_error:
                    print(f"Failed to delete temp file {path}: {cleanup_error}")
    
import tempfile
@csrf_exempt
def emailInvoice(request):
    if request.method == "POST":
        data = json.loads(request.body)
        invoice_url = data.get("invoice_url")

        if not invoice_url:
            return JsonResponse({"error": "Invoice URL is missing."}, status=400)
        invoice_filename = invoice_url.split("/")[-1]
        temp_file_path = None  
        try:
            response = requests.get(invoice_url)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name  
            subject = 'Tekbind Course Invoice'
            from_email = 'support@tekbind.com'
            to = [request.user.email]
            cc_recipients = ['tekbindinvoice@gmail.com', 'devops6868@gmail.com']
            html_content = f"""
            <p>Dear <strong>{request.user.first_name}</strong>,</p>

            <p>Thank you for successfully completing the course. Please find your invoice attached for your records.</p>

            <p>If you have any questions or require further assistance, please feel free to contact our support team at <strong>+91 96636 54114</strong>.</p>

            <p>Best regards,</p>
            <p><strong>Tekbind Team</strong></p>
            """

            msg = EmailMessage(subject, html_content, from_email, to, cc=cc_recipients)
            msg.content_subtype = "html"  
            msg.attach_file(temp_file_path)
            msg.send()

            return JsonResponse({"message": "Invoice email sent successfully with attachment."})

        except requests.RequestException as e:
            return JsonResponse({"error": f"Failed to download invoice: {str(e)}"}, status=500)

        except Exception as e:
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as cleanup_error:
                    print(f"Failed to delete temp file: {cleanup_error}")

@login_required(login_url='/login/')
def profile_view(request, user_id=None):
    template = "profile.html"
    search_candidate = request.POST.get('search_candidate', None)
    if search_candidate:
        search_candidate_id = search_candidate.split('-')[-1]
        user_id = profile.objects.get(id=search_candidate_id).user.id

    if not user_id or request.user.is_staff == False:
        user_id = request.user.id

    upload_path = "/".join(["media", "documents", str(user_id)])
    try:
        if os.path.exists(upload_path):
            shutil.rmtree(upload_path)
    except:
        pass

    data = profile.objects.filter(user_id=user_id)
    master = education.objects.filter(user_id=user_id, course_level='master')
    plus_two_diploma = education.objects.filter(user_id=user_id, course_level='plus_two_diploma')
    degree = education.objects.filter(user_id=user_id, course_level='degree')
    sslc = education.objects.filter(user_id=user_id, course_level='sslc')
    exp = experience.objects.filter(user_id=user_id)
    docs = list(documents.objects.filter(user_id=user_id).values())
    courses = Payment.objects.filter(userid=user_id, paid=True)
    invoice_download_url =None
    course_list=[]
    for course in courses:
        course_dict = model_to_dict(course)
        file_obj = course.invoice_link
        if file_obj:
            if hasattr(file_obj, 'url') and 'upload' in file_obj.url:
                url = file_obj.url  
                url_part = url.split('upload', 1)
                invoice_download_url = f"{url_part[0]}upload/fl_attachment{url_part[1]}"
        
                course_dict['invoice_download_url'] = invoice_download_url
            course_dict['course_id']=course.course_id
            course_list.append(course_dict)
    for d in docs:
        file_obj = d.get('file_location')
        if hasattr(file_obj, 'url') and 'upload' in file_obj.url:
            url_part = file_obj.url.split('upload', 1)
            d['file_link'] = file_obj
            d['file_download_url'] = f"{url_part[0]}upload/fl_attachment{url_part[1]}"

    if data.count():
        data = data[0]
    if master.count():
        master = master[0]
    if plus_two_diploma.count():
        plus_two_diploma = plus_two_diploma[0]
    if degree.count():
        degree = degree[0]
    if sslc.count():
        sslc = sslc[0]

    all_users = profile.objects.all()

    context = {'data': data,
               'master': master,
               'degree': degree,
               'plus_two_diploma': plus_two_diploma,
               'sslc': sslc,
               'documents': docs,
               'experience_list': exp,
               'all_users': all_users,
               'my_courses':course_list
               }

    return render(request, template, context)


def register_api(request, key="CREATE", user_id=None):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    email = request.POST.get('email', '')
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
    profile_image = request.POST.get('profile_image', "")
    interests = request.POST.get('interests', "")
    skill_set = request.POST.get('skill_set', "")
    about = request.POST.get('about', "")
    present_address = request.POST.get('present_address', "")
    permanent_address = request.POST.get('permanent_address', "")
    profile_status = request.POST.get('profile_status', "")
    uan = request.POST.get('uan', "")

    if email:
        user_qs = User.objects.filter(username=email)
    else:
        user_qs = request.user
        email = request.user.email

    if key == 'CREATE':
        if user_qs and user_qs.exists():
            return JsonResponse({"error": "User already exists"}, status=400)
        else:
            user = User.objects.create_user(username=email, email=email, password=password, first_name=first_name)
            if user:
                login(request, user)
                key = 'UPDATE'
            else:
                return JsonResponse({"error": "User creation failed"}, status=500)
    else:
        user = user_qs if isinstance(user_qs, User) else user_qs.first()

    if key == 'UPDATE':
        if request.user.is_anonymous:
            return JsonResponse({"error": "Unauthorized access"}, status=403)

        if not user_id:
            user_id = request.POST.get('user_id', None)

        if not user_id or not request.user.is_staff:
            user_id = request.user.id

        try:
            current_user = User.objects.get(id=user_id)
            current_user_profile = profile.objects.get(user_id=user_id)
        except (User.DoesNotExist, profile.DoesNotExist):
            return JsonResponse({"error": "User or profile not found"}, status=404)

        current_user.profile.profile_status = False
        current_user.profile.save()

        if email.strip():
            current_user.email = email.strip()
            current_user.username = email.strip()
        if first_name.strip():
            current_user.first_name = first_name
        if last_name.strip():
            current_user.last_name = last_name
        current_user.save()

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
        }

        # Only update non-empty fields
        for field, value in update_fields.items():
            if value.strip():
                setattr(current_user_profile, field, value)

        current_user_profile.save()

    return redirect('profile_view', user_id)

def login_api(request):
    email = request.POST.get('email', '')
    password = request.POST.get('password', '')
    try:
        user = User.objects.get(email=email)
        user = authenticate(username=user, password=password)
        login(request, user)
        return redirect(profile_view)
    except:
        return login_view(request, "Invalid Credentials!!")


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

    if not user_id or request.user.is_staff == False:
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

    if not user_id or request.user.is_staff == False:
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

    if not user_id or request.user.is_staff == False:
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
    exp = experience.objects.filter(id=experience_id, user_id=request.user.id)
    if exp.count():
        exp = exp[0]

    context = {"experience": exp}
    template = "experience.html"
    return render(request, template, context)


def delete_experience(request, experience_id=0):
    exp = experience.objects.filter(id=experience_id, user_id=request.user.id)
    exp.delete()
    return redirect('profile_view')


@login_required(login_url='/login/')
def download_view(request, user_id=None):
    if not user_id or not request.user.is_staff:
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
