from django.db import models


class CostQuerySet(models.QuerySet):
    def get_costs(self):
        return self.filter()
