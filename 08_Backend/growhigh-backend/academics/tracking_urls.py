from django.urls import path
from rest_framework.routers import DefaultRouter

from .tracking import (CareerGoalViewSet, GuideQuestionViewSet, GuideQuizView, GuideSubmissionViewSet, GuideSubmitView, GuideTaskSettingView,
                       GuideTasksView, NoticeView, QuizCountsView, QuizPerformanceView, StudentReportView)

router = DefaultRouter()
router.register("guide-questions", GuideQuestionViewSet, basename="guide-question")
router.register("guide-submissions", GuideSubmissionViewSet, basename="guide-submission")
router.register("career-goals", CareerGoalViewSet, basename="career-goal")

urlpatterns = [
    path("guide-quiz-counts/", QuizCountsView.as_view()),
    path("quiz-performance/", QuizPerformanceView.as_view()),
    path("performance/student/<int:pk>/", StudentReportView.as_view()),
    path("notices/", NoticeView.as_view()),
    path("notices/read/", NoticeView.as_view()),
    path("guide-tasks/", GuideTasksView.as_view()),
    path("guides/<int:pk>/quiz/", GuideQuizView.as_view()),
    path("guides/<int:pk>/submit/", GuideSubmitView.as_view()),
    path("guides/<int:pk>/task-setting/", GuideTaskSettingView.as_view()),
] + router.urls
