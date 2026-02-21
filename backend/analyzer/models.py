from django.db import models

# Create your models here.
class QuestionGroup(models.Model):
    representative = models.TextField()
    priority = models.CharField(max_length=10)
    count = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.representative[:80]

class QuestionVariant(models.Model):
    group = models.ForeignKey(
        QuestionGroup,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    text = models.TextField()
    source_file = models.CharField(max_length=255)

    def __str__(self):
        return self.text[:80]