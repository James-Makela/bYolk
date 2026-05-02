from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .models import Category
from .forms import CategoryForm


# Create your views here.
def home(request):
    return render(request, 'base.html')

@login_required
def categories(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'category/index.html', {
        "categories": categories
    })

@login_required
def create_category(request):
    if request.method == "POST":
        # Create a form instance and populate it with data from the rrequest
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, "Category added!")
            return HttpResponseRedirect("/core/categories/")

    # If a GET or any other method create a blank form
    else:
        form = CategoryForm()

    return render(request, "category/forms/add_category_form.html", {"form": form})

@login_required
def delete_category(request, pk):
    cost = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == "POST":
        cost.delete()
        messages.success(request, "Category deleted")
    
    return HttpResponseRedirect("/core/categories/")
