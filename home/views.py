import os
import re
import shutil

import boto3
from botocore.config import Config
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from s3transfer import TransferConfig
from django.db.models import Value
from zipfile import ZipFile, ZIP_DEFLATED
import urllib.request

from home.models import profile, education, documents, experience


def home_view(request):
    if request.user.is_anonymous:
        template = "index.html"
        context = {}
        return render(request, template, context)
    else:
        return redirect(profile_view)


def register_view(request, message=''):
    template = "register.html"
    context = {"message": message}
    return render(request, template, context)


def login_view(request, message=''):
    template = "login.html"
    context = {"message": message}
    return render(request, template, context)


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
    print(os.path.join(os.getcwd(), upload_path))
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
    for d in docs:
        d['file_link'] = get_s3_file_name(d.get('file_location'))

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
               'all_users': all_users
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

    data_exists = documents.objects.filter(user_id=user_id, file_title=file_title)

    if not data_exists.count():
        newDocument = documents(user_id=user_id,
                                file_title=file_title,
                                file_location=upload_file(input_file, file_title, user_id))
        newDocument.save()

    else:
        data_exists.update(file_location=upload_file(input_file, file_title, user_id))

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
    if not user_id or request.user.is_staff == False:
        user_id = request.user.id
    data_exists = documents.objects.filter(user_id=user_id)
    usr = User.objects.get(id=user_id)
    usr = usr.first_name.replace(' ', '_') + "_" + usr.last_name.replace(' ', '_')
    if data_exists:
        upload_path = os.path.join("media", "documents")
        upload_path = os.path.join(upload_path, str(user_id))
        upload_path = os.path.join(os.getcwd(), upload_path)
        if not os.path.exists(upload_path):
            os.umask(0)
            os.makedirs(upload_path, mode=0o777)

        with ZipFile(os.path.join(upload_path, usr + ".zip"), 'w', ZIP_DEFLATED) as myzip:
            for d in data_exists:
                file_path = os.path.join(upload_path, d.file_title + "." + d.file_location.split('.')[-1])
                urllib.request.urlretrieve(get_s3_file_name(d.file_location), file_path)
                myzip.write(file_path, d.file_title + "." + d.file_location.split('.')[-1])

    response = ""
    with open(os.path.join(upload_path, usr + ".zip"), 'rb') as f:
        response = HttpResponse(f.read())
        response['Content-Disposition'] = 'attachment; filename="' + usr + '.zip"'

    return response
