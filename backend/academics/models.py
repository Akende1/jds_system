from django.db import models
from django.core.exceptions import ValidationError
from administration.models import User, ClassRoom, Student, AcademicYear, Term, Grade


class Subject(models.Model):
    """Subjects taught in the school"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_elective = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.code} - {self.name}"


class SubjectAllocation(models.Model):
    """Assigns subjects to specific grades/classes"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='allocations')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='subject_allocations')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               limit_choices_to={'user_type': 'teacher'},
                               related_name='subject_assignments')
    periods_per_week = models.IntegerField(default=5)
    
    class Meta:
        unique_together = ['subject', 'grade', 'academic_year']
        ordering = ['grade', 'subject']
        
    def __str__(self):
        return f"{self.subject.name} - {self.grade.name} ({self.academic_year.name})"


class Syllabus(models.Model):
    """Curriculum/Syllabus for subjects"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='syllabi')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='syllabi')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    topics = models.TextField(help_text="List of topics to be covered")
    learning_objectives = models.TextField()
    
    document = models.FileField(upload_to='syllabus/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Syllabi'
        ordering = ['grade', 'subject', 'term']
        
    def __str__(self):
        return f"{self.subject.name} - {self.grade.name} ({self.term})"


class Assignment(models.Model):
    """Assignments given to students"""
    ASSIGNMENT_TYPE_CHOICES = (
        ('homework', 'Homework'),
        ('project', 'Project'),
        ('classwork', 'Classwork'),
        ('research', 'Research'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, 
                               limit_choices_to={'user_type': 'teacher'},
                               related_name='assignments_created')
    
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='homework')
    max_marks = models.IntegerField(default=100)
    
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    attachment = models.FileField(upload_to='assignments/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-assigned_date']
        
    def __str__(self):
        return f"{self.title} - {self.classroom}"


class AssignmentSubmission(models.Model):
    """Student submissions for assignments"""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions')
    
    submission_date = models.DateTimeField(auto_now_add=True)
    submission_file = models.FileField(upload_to='submissions/', null=True, blank=True)
    submission_text = models.TextField(blank=True)
    
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 limit_choices_to={'user_type': 'teacher'},
                                 related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    
    is_late = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-submission_date']
        
    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        # Check if submission is late
        if self.assignment.due_date and self.submission_date:
            self.is_late = self.submission_date.date() > self.assignment.due_date
        super().save(*args, **kwargs)


class Exam(models.Model):
    """Examinations/Tests"""
    EXAM_TYPE_CHOICES = (
        ('mid_term', 'Mid-Term Test'),
        ('end_term', 'End of Term Exam'),
        ('quiz', 'Quiz'),
        ('mock', 'Mock Exam'),
        ('final', 'Final Exam'),
    )
    
    name = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='exams')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='exams')
    
    exam_date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.IntegerField()
    max_marks = models.IntegerField(default=100)
    pass_marks = models.IntegerField(default=40)
    
    instructions = models.TextField(blank=True)
    syllabus_covered = models.TextField(blank=True)

    is_administered = models.BooleanField(default=False)
    administered_at = models.DateTimeField(null=True, blank=True)
    administered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administered_exams',
    )
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  limit_choices_to={'user_type': 'teacher'})
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-exam_date']
        
    def __str__(self):
        return f"{self.name} - {self.subject.name} ({self.classroom})"


class ExamResult(models.Model):
    """Individual exam results for students"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2, blank=True)
    remarks = models.TextField(blank=True)
    
    is_absent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['exam', 'student']
        ordering = ['-marks_obtained']
        
    def __str__(self):
        return f"{self.student.full_name} - {self.exam.name}: {self.marks_obtained}/{self.exam.max_marks}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate grade
        if not self.is_absent and self.marks_obtained is not None:
            percentage = (self.marks_obtained / self.exam.max_marks) * 100
            if percentage >= 90:
                self.grade = 'A+'
            elif percentage >= 80:
                self.grade = 'A'
            elif percentage >= 70:
                self.grade = 'B'
            elif percentage >= 60:
                self.grade = 'C'
            elif percentage >= 50:
                self.grade = 'D'
            elif percentage >= 40:
                self.grade = 'E'
            else:
                self.grade = 'F'
        super().save(*args, **kwargs)


class GradingScheme(models.Model):
    """Grading scheme for the school"""
    name = models.CharField(max_length=100)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    remarks = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['-min_percentage']
        
    def __str__(self):
        return f"{self.grade}: {self.min_percentage}% - {self.max_percentage}%"


class ReportCard(models.Model):
    """Student report cards"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='report_cards')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='report_cards')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    
    overall_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_grade = models.CharField(max_length=2, blank=True)
    position_in_class = models.IntegerField(null=True, blank=True)
    
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    conduct_grade = models.CharField(max_length=2, blank=True)
    
    teacher_remarks = models.TextField(blank=True)
    principal_remarks = models.TextField(blank=True)
    
    next_term_begins = models.DateField(null=True, blank=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'term']
        ordering = ['-term', 'position_in_class']
        
    def __str__(self):
        return f"{self.student.full_name} - {self.term}"


class Timetable(models.Model):
    """Weekly class timetable for day-to-day lesson planning."""

    DAY_OF_WEEK_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )

    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='timetable_entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable_entries')
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'teacher'},
        related_name='timetable_assignments',
    )
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='timetable_entries')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='timetable_entries', null=True, blank=True)
    day_of_week = models.CharField(max_length=10, choices=DAY_OF_WEEK_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'start_time', 'classroom__grade__level', 'classroom__section']
        unique_together = ['classroom', 'academic_year', 'term', 'day_of_week', 'start_time']

    def clean(self):
        super().clean()

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})

        overlap_filter = models.Q(
            academic_year=self.academic_year,
            term=self.term,
            day_of_week=self.day_of_week,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )

        classroom_conflict = Timetable.objects.filter(
            overlap_filter,
            classroom=self.classroom,
        )
        teacher_conflict = Timetable.objects.filter(
            overlap_filter,
            teacher=self.teacher,
        ) if self.teacher else Timetable.objects.none()
        room_conflict = Timetable.objects.filter(
            overlap_filter,
            room=self.room,
        ) if self.room else Timetable.objects.none()

        if self.pk:
            classroom_conflict = classroom_conflict.exclude(pk=self.pk)
            teacher_conflict = teacher_conflict.exclude(pk=self.pk)
            room_conflict = room_conflict.exclude(pk=self.pk)

        errors = {}
        if classroom_conflict.exists():
            errors['classroom'] = 'This class already has a lesson scheduled at this time.'
        if teacher_conflict.exists():
            errors['teacher'] = 'This teacher is already booked at this time.'
        if room_conflict.exists():
            errors['room'] = 'This room is already booked at this time.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.classroom} - {self.get_day_of_week_display()} {self.start_time}"

