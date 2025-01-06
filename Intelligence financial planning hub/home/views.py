from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Expense, UserProfile
from django.db.models import Sum
from decimal import Decimal
from django.http import HttpResponse
from io import BytesIO
from xhtml2pdf import pisa
import plotly.graph_objects as go

def home_page(request):
    return render(request, 'home/home.html')


# Expenses page
@login_required(login_url='/login/')
def expenses(request):
    if request.method == 'POST':
        data = request.POST
        category = data.get('category')
        amount = data.get('amount')
        date = data.get('date')

        if not category or not amount or not date:
            messages.error(request, "All fields are required.")
            return redirect('expenses')

        try:
            amount = Decimal(amount)
        except ValueError:
            messages.error(request, "Invalid amount.")
            return redirect('expenses')

        Expense.objects.create(
            category=category,
            amount=amount,
            date=date,
            user=request.user
        )
        return redirect('expenses')

    queryset = Expense.objects.filter(user=request.user).order_by('-date')
    total_amount = queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        salary = user_profile.salary
        monthly_budget = user_profile.monthly_budget
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please complete your profile.")
        return redirect('register')

    remaining_balance = Decimal(salary) - total_amount

    context = {
        'expenses': queryset,
        'total_amount': total_amount,
        'salary': salary,
        'monthly_budget': monthly_budget,
        'remaining_balance': remaining_balance,
    }

    return render(request, 'expenses.html', context)

# Update Expense
@login_required(login_url='/login/')
def update_expense(request, id):
    try:
        expense = Expense.objects.get(id=id, user=request.user)
    except Expense.DoesNotExist:
        messages.error(request, "Expense not found or unauthorized access.")
        return redirect('expenses')

    if request.method == 'POST':
        data = request.POST
        category = data.get('category')
        amount = data.get('amount')
        date = data.get('date')

        if not category or not amount or not date:
            messages.error(request, "All fields are required.")
            return redirect('update_expense', id=id)

        try:
            amount = Decimal(amount)
        except ValueError:
            messages.error(request, "Invalid amount.")
            return redirect('update_expense', id=id)

        expense.category = category
        expense.amount = amount
        expense.date = date
        expense.save()

        messages.success(request, "Expense updated successfully.")
        return redirect('expenses')

    context = {'expense': expense}
    return render(request, 'update_expense.html', context)

# Delete Expense
@login_required(login_url='/login/')
def delete_expense(request, id):
    try:
        expense = Expense.objects.get(id=id, user=request.user)
    except Expense.DoesNotExist:
        messages.error(request, "Expense not found or you don't have permission to delete this expense.")
        return redirect('expenses')

    expense.delete()
    return redirect('expenses')

# Login Page
def login_page(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_auth = authenticate(username=username, password=password)
        if user_auth:
            login(request, user_auth)
            return redirect('expenses')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login')
    return render(request, "login.html")

# Register Page
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        salary = request.POST.get('salary')
        monthly_budget = request.POST.get('monthly_budget')

        try:
            salary = float(salary)
        except ValueError:
            salary = 0

        try:
            monthly_budget = float(monthly_budget)
        except ValueError:
            monthly_budget = 0

        user = User.objects.create_user(username=username, password=password, email=email)

        if not UserProfile.objects.filter(user=user).exists():
            UserProfile.objects.create(user=user, salary=salary, monthly_budget=monthly_budget)
            messages.success(request, "Registration successful!")
        else:
            messages.error(request, "User profile already exists!")

        return redirect('login')

    return render(request, 'register.html')

# Logout
def custom_logout(request):
    logout(request)
    return redirect('login')

# Generate PDF
@login_required(login_url='/login/')
def pdf(request):
    queryset = Expense.objects.filter(user=request.user)

    if request.GET.get('search'):
        queryset = queryset.filter(category__icontains=request.GET.get('search'))

    total_sum = queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)

    context = {
        'expenses': queryset,
        'total_sum': total_sum,
        'username': request.user.username
    }

    template_path = 'pdf.html'
    html = render(request, template_path, context)

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html.content, dest=buffer, link_callback=None)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', content_type='text/plain')

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{request.user.username}_expense_report.pdf"'
    buffer.close()
    return response

# Visualization
@login_required(login_url='/login/')
def visualize_expenses(request):
    category_expenses = Expense.objects.filter(user=request.user).values('category').annotate(total_amount=Sum('amount'))
    categories = [expense['category'] for expense in category_expenses]
    totals = [expense['total_amount'] for expense in category_expenses]

    pie_chart = go.Figure(go.Pie(labels=categories, values=totals, hole=0.3))
    pie_chart.update_layout(title='Expense Distribution by Category')
    pie_chart_html = pie_chart.to_html(full_html=False)

    bar_chart = go.Figure([go.Bar(x=categories, y=totals)])
    bar_chart.update_layout(title="Expense Breakdown by Category", xaxis_title="Category", yaxis_title="Total Amount")
    bar_chart_html = bar_chart.to_html(full_html=False)

    return render(request, 'visualization.html', {
        'pie_chart_html': pie_chart_html,
        'bar_chart_html': bar_chart_html,
        'category_expenses': category_expenses,
    })

# Financial Overview
@login_required(login_url='/login/')
def financial_overview(request):
    expenses = Expense.objects.filter(user=request.user)

    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        budget_threshold = user_profile.monthly_budget
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please complete your profile.")
        return redirect('register')

    gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_expenses,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Total Expenses Overview"},
        delta={'reference': budget_threshold},
        gauge={
            'axis': {'range': [0, max(budget_threshold * 2, total_expenses * 1.2)]},
            'steps': [
                {'range': [0, budget_threshold], 'color': "lightgreen"},
                {'range': [budget_threshold, budget_threshold * 1.5], 'color': "orange"},
                {'range': [budget_threshold * 1.5, max(budget_threshold * 2, total_expenses * 1.2)], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': budget_threshold
            }
        }
    ))
    gauge_html = gauge.to_html(full_html=False)

    category_expenses = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    treemap = go.Figure(go.Treemap(
        labels=[expense['category'] for expense in category_expenses],
        parents=[""] * len(category_expenses),
        values=[expense['total'] for expense in category_expenses],
        textinfo="label+value"
    ))
    tree_map_html = treemap.to_html(full_html=False) if category_expenses else None

    tips = []
    if total_expenses > budget_threshold:
        tips.append("Your spending exceeds the monthly budget. Consider reducing discretionary expenses.")
    if len(category_expenses) > 0 and max(expense['total'] for expense in category_expenses) > budget_threshold * 0.3:
        tips.append("A single category constitutes a large part of your spending. Review and optimize.")
    tips.append("Track your daily expenses to identify opportunities for savings.")

    context = {
        'gauge_html': gauge_html,
        'tree_map_html': tree_map_html,
        'monthly_expenses': total_expenses,
        'budget_threshold': budget_threshold,
        'tips': tips,
    }

    return render(request, 'financial_overview.html', context)
