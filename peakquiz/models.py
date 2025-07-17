from django.db import models


class Peak(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    aliases = models.TextField(null=True)
    dominance_peak = models.CharField(max_length=255, null=True)
    dominance_distance = models.FloatField(null=True)
    prominence_distance = models.FloatField(null=True)
    prominence_peak = models.CharField(max_length=255, null=True)
    region = models.CharField(max_length=255, null=True)
    elevation = models.IntegerField(null=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.elevation}m)"

class Picture(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.URLField(unique=True)
    peak = models.ForeignKey(Peak, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.url
    

