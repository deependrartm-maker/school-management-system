from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from accounts.decorators import role_required
from accounts.models import CustomUser
from accounts.permissions import can_view_student

from .models import StudentProfile, ParentProfile

# ✅ Hardcoded choices for Class & Section

CLASS_CHOICES = [('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5')]
SECTION_CHOICES = [('Jasmine','Jasmine'), ('Lotus','Lotus'), ('Lily','Lily'), ('Rose','Rose')]

@login_required
def add_student(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name").strip()
        email = request.POST.get("email").strip()
        admission_no = request.POST.get("admission_no").strip()
        student_class = request.POST.get("student_class")
        section = request.POST.get("section")
        dob = request.POST.get("dob")
        photo = request.FILES.get("photo")
        parent_name = request.POST.get("parent_name").strip()
        parent_contact = request.POST.get("parent_contact").strip()
        address = request.POST.get("address").strip()

        # Validate required fields
        if not all([full_name, email, admission_no, student_class, section, dob, parent_name, parent_contact]):
            messages.error(request, "Please fill all required fields.")
            return redirect("add_student")

        # Split full name
        names = full_name.split(maxsplit=1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ""

        # Create user
        user = CustomUser.objects.create_user(
            username=admission_no,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password="student123",
            user_type="STUDENT"
        )

        # Create StudentProfile
        StudentProfile.objects.create(
            user=user,
            admission_no=admission_no,
            student_class=student_class,
            section=section,
            dob=dob,
            photo=photo,
            address=address
        )

        # Create ParentProfile
        ParentProfile.objects.create(
            student=user,
            name=parent_name,
            contact_number=parent_contact
        )

        messages.success(request, f"Student '{full_name}' added successfully!")
        return redirect("add_student")

    # ✅ Pass class & section to template
    
    context = {
        "class_choices": CLASS_CHOICES,
        "section_choices": SECTION_CHOICES
    }
    return render(request, "profiles/add_student.html", context)


def student_detail(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    if not can_view_student(request.user, student):
        return HttpResponseForbidden("Not allowed")
    return render(request, "student/detail.html", {"student": student})


@login_required
def my_profile(request):
    user = request.user
    if user.user_type != "STUDENT":
        raise Http404

    try:
        student_profile = StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist:
        raise Http404

    if not can_view_student(user, student_profile):
        raise Http404

    return render(request, "student/detail.html", {"student": student_profile})


@role_required("TEACHER")
def teacher_student_list(request):
    students = StudentProfile.objects.select_related("user").order_by("admission_no")
    query = request.GET.get("q", "").strip()

    if query:
        students = students.filter(
            Q(admission_no__icontains=query) |
            Q(user__email__icontains=query) |
            Q(student_class__icontains=query) |
            Q(section__icontains=query)
        )

    paginator = Paginator(students, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "students": page_obj,
        "query": query,
    }
    return render(request, "student/teacher_list.html", context)