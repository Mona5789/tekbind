from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from cloudinary.models import CloudinaryField

# Create your models here.
CANDIDATE = "CANDIDATE"
OTHER = "OTHER"
BLANK = ""
DEFAULT_IMAGE = "DEFAULT_IMAGE"


class profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    group = models.CharField(max_length=300, default=CANDIDATE, null=True)
    pan_name = models.CharField(max_length=300, default=BLANK, null=True)
    phone_number = models.CharField(max_length=300, default=BLANK, null=True)
    whatsapp_number = models.CharField(max_length=300, default=BLANK, null=True)
    dob = models.CharField(max_length=300, default=BLANK, null=True)
    father = models.CharField(max_length=300, default=BLANK, null=True)
    mother = models.CharField(max_length=300, default=BLANK, null=True)
    aadhar = models.CharField(max_length=300, default=BLANK, null=True)
    pan = models.CharField(max_length=300, default=BLANK, null=True)
    passport = models.CharField(max_length=300, default=BLANK, null=True)
    marital = models.CharField(max_length=300, default=BLANK, null=True)
    gender = models.CharField(max_length=300, default=BLANK, null=True)
    blood = models.CharField(max_length=300, default=BLANK, null=True)
    batch = models.CharField(max_length=300, default=BLANK, null=True)
    batch_month = models.CharField(max_length=300, default=BLANK, null=True)
    batch_timings = models.CharField(max_length=300, default=BLANK, null=True)
    batch_year = models.CharField(max_length=300, default=BLANK, null=True)
    reference = models.CharField(max_length=300, default=BLANK, null=True)
    profile_image = models.TextField(default=DEFAULT_IMAGE)
    interests = models.TextField(default=BLANK, null=True)
    skill_set = models.CharField(max_length=300, default=BLANK, null=True)
    about = models.TextField(default=BLANK, null=True)
    present_address = models.TextField(default=BLANK, null=True)
    permanent_address = models.TextField(default=BLANK, null=True)
    uan = models.TextField(default=BLANK, null=True)
    profile_status = models.BooleanField(default=True)
    date_modified = models.DateTimeField(auto_now_add=True, editable=False, null=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            profile.objects.create(user=instance, id=instance.id)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def __str__(self):
        return str(self.user.id) + "\t" + self.user.username


class education(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='education')
    course_level = models.TextField(default=BLANK, null=True)
    course = models.TextField(default=BLANK, null=True)
    specialization = models.TextField(default=BLANK, null=True)
    college = models.TextField(default=BLANK, null=True)
    university = models.TextField(default=BLANK, null=True)
    year_in = models.TextField(default=BLANK, null=True)
    year_out = models.TextField(default=BLANK, null=True)
    percentage = models.TextField(default=BLANK, null=True)

    def __str__(self):
        return str(self.user.id) + "\t" + self.user.username + "\t" + self.course


class experience(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experience')
    company = models.TextField(default=BLANK, null=True)
    designation = models.TextField(default=BLANK, null=True)
    domain = models.TextField(default=BLANK, null=True)
    date_in = models.TextField(default=BLANK, null=True)
    date_out = models.TextField(default=BLANK, null=True)

    def __str__(self):
        return str(self.user.id) + "\t" + self.user.username


class documents(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document')
    file_title = models.TextField(default=BLANK, null=True)
    file_location = CloudinaryField('document', blank=True, null=True)

    def __str__(self):
        return str(self.user.id) + "\t" + self.user.file_title
    
class course(models.Model):
    COURSETYPES = (
        ("DevOps","DevOps"),
        ("Full stack", "Full stack")
    )
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=1000, null=True, default="")
    course_type = models.CharField(max_length=255, null=True, blank=True, choices=COURSETYPES)
    description = models.TextField(default="", null=True, blank=True)
    course_concept = models.TextField(default="", null=True, blank=True)
    course_eligibility = models.TextField(default="", null=True, blank=True)
    course_format = models.TextField(default="", null=True, blank=True)
    course_slogan = models.TextField(default="", null=True, blank=True)
    keywords = models.CharField(max_length=1000, null=True, default="", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    duration = models.CharField(max_length=1000, null=True, default="", blank=True)
    image = CloudinaryField('courses', blank=True, null=True)
    date_modified = models.DateTimeField(auto_now_add=True, editable=False, null=True, blank=True)

    def _str_(self):
        return f'{self.title}'
    
class Payment(models.Model):
    course_id = models.ForeignKey(course, on_delete=models.CASCADE, null=True, blank=True)
    userid = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default="", blank=True)
    date = models.DateTimeField(null=True, blank=True)
    order_id = models.CharField(max_length=100, unique=True) 
    payment_id = models.TextField(blank=True, null=True) 
    amount = models.DecimalField(max_digits=10, decimal_places=2) 
    invoice_link = CloudinaryField('invoices-pdf',resource_type='raw', null=True, blank=True)
    paid = models.BooleanField(default=False) 

    def __str__(self):
        return f"Order {self.order_id} - {'Paid' if self.paid else 'Pending'}"
