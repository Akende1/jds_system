from django.contrib import admin
from .models import Course, Lesson, DiscussionForum, ForumPost


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'classroom', 'instructor', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at', 'subject']
    search_fields = ['title', 'instructor__first_name']
    raw_id_fields = ['instructor']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'lesson_type', 'order', 'is_published']
    list_filter = ['lesson_type', 'is_published', 'course']
    search_fields = ['title', 'course__title']


@admin.register(DiscussionForum)
class DiscussionForumAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'created_by', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['title', 'course__title']
    raw_id_fields = ['created_by']


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ['forum', 'author', 'posted_at']
    list_filter = ['forum', 'posted_at']
    search_fields = ['content', 'forum__title']
    raw_id_fields = ['author', 'parent_post']
