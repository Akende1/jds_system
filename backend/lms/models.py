from django.db import models
from django.utils import timezone
from administration.models import User, ClassRoom, Student
from academics.models import Subject


class Course(models.Model):
    """E-learning courses"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='courses')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE,
                                  limit_choices_to={'user_type': 'teacher'},
                                  related_name='courses_taught')
    
    thumbnail = models.ImageField(upload_to='courses/', null=True, blank=True)
    is_published = models.BooleanField(default=False)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.subject.name}"


class Lesson(models.Model):
    """Individual lessons within a course"""
    LESSON_TYPE_CHOICES = (
        ('video', 'Video'),
        ('document', 'Document'),
        ('presentation', 'Presentation'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField()
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES)
    
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    file_attachment = models.FileField(upload_to='lessons/', null=True, blank=True)
    
    order = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=0)
    
    is_published = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class LessonProgress(models.Model):
    """Track student progress through lessons"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    time_spent_minutes = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'lesson']
        ordering = ['lesson']
        verbose_name_plural = 'Lesson Progress Records'
        
    def __str__(self):
        return f"{self.student.full_name} - {self.lesson.title}"


class OnlineQuiz(models.Model):
    """Online quizzes"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='quizzes')
    
    max_marks = models.IntegerField(default=100)
    pass_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40)
    time_limit_minutes = models.IntegerField(default=60)
    
    max_attempts = models.IntegerField(default=3)
    show_results_immediately = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Online Quizzes'
        
    def __str__(self):
        return f"{self.title} - {self.course.title}"


class QuizQuestion(models.Model):
    """Questions for online quizzes"""
    QUESTION_TYPE_CHOICES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    )
    
    quiz = models.ForeignKey(OnlineQuiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    
    question_text = models.TextField()
    marks = models.IntegerField(default=1)
    
    option_a = models.CharField(max_length=200, blank=True)
    option_b = models.CharField(max_length=200, blank=True)
    option_c = models.CharField(max_length=200, blank=True)
    option_d = models.CharField(max_length=200, blank=True)
    
    correct_answer = models.CharField(max_length=200, blank=True)
    explanation = models.TextField(blank=True)
    
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['quiz', 'order']
        
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"


class QuizAttempt(models.Model):
    """Student quiz attempts"""
    quiz = models.ForeignKey(OnlineQuiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_attempts')
    
    attempt_number = models.IntegerField(default=1)
    
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    is_passed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.student.full_name} - {self.quiz.title} (Attempt {self.attempt_number})"


class QuizAnswer(models.Model):
    """Student answers to quiz questions"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    
    answer_text = models.TextField()
    is_correct = models.BooleanField(null=True, blank=True)
    marks_awarded = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['attempt', 'question']
        
    def __str__(self):
        return f"{self.attempt.student.full_name} - Q{self.question.order}"


class DiscussionForum(models.Model):
    """Discussion forums for courses"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='forums')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class ForumPost(models.Model):
    """Posts within discussion forums"""
    forum = models.ForeignKey(DiscussionForum, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    
    content = models.TextField()
    attachment = models.FileField(upload_to='forum_attachments/', null=True, blank=True)
    
    parent_post = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='replies')
    
    posted_at = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    is_pinned = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_pinned', '-posted_at']
        
    def __str__(self):
        return f"{self.author.get_full_name()} - {self.forum.title}"

