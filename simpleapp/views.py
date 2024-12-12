from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.core.cache import cache
from django.utils.translation import gettext as _

from .filters import ProductFilter
from .forms import ProductForm
from .models import Product, Subscription, Category
from .tasks import hello, printer


class ProductsList(ListView):
    # Указываем модель, объекты которой мы будем выводить
    model = Product
    # Поле, которое будет использоваться для сортировки объектов
    ordering = 'name'
    # Указываем имя шаблона, в котором будут все инструкции о том,
    # как именно пользователю должны быть показаны наши объекты
    template_name = 'products.html'
    # Это имя списка, в котором будут лежать все объекты.
    # Его надо указать, чтобы обратиться к списку объектов в html-шаблоне.
    context_object_name = 'products'
    paginate_by = 3  # вот так мы можем указать количество записей на странице

    def get_queryset(self):
        # Получаем обычный запрос
        queryset = super().get_queryset()
        # Используем наш класс фильтрации.
        # self.request.GET содержит объект QueryDict, который мы рассматривали
        # в этом юните ранее.
        # Сохраняем нашу фильтрацию в объекте класса,
        # чтобы потом добавить в контекст и использовать в шаблоне.
        self.filterset = ProductFilter(self.request.GET, queryset)
        # Возвращаем из функции отфильтрованный список товаров
        return self.filterset.qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = datetime.utcnow()
        context['next_sale'] = None
        # Добавляем в контекст объект фильтрации.
        context['filterset'] = self.filterset
        return context


class ProductDetail(DetailView):
    template_name = 'product.html'
    queryset = Product.objects.all()

    def get_object(self, *args, **kwargs):
        obj = cache.get(f"product-{self.kwargs["pk"]}", None)

        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f"product-{self.kwargs["pk"]}", obj)
        return obj


# Добавляем новое представление для создания товаров.
class ProductCreate(PermissionRequiredMixin, CreateView):
    permission_required = ('simpleapp.add_product',)
    # Указываем нашу разработанную форму
    form_class = ProductForm
    # модель товаров
    model = Product
    # и новый шаблон, в котором используется форма.
    template_name = 'product_edit.html'


# Добавляем представление для изменения товара.
class ProductUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = ('simpleapp.change_product',)
    form_class = ProductForm
    model = Product
    template_name = 'product_edit.html'


# Представление удаляющее товар.
class ProductDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('simpleapp.delete_product',)
    model = Product
    template_name = 'product_delete.html'
    success_url = reverse_lazy('product_list')


@login_required
@csrf_protect
def subscriptions(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = Category.objects.get(id=category_id)
        action = request.POST.get('action')

        if action == 'subscribe':
            Subscription.objects.create(user=request.user, category=category)
        elif action == 'unsubscribe':
            Subscription.objects.filter(
                user=request.user,
                category=category,
            ).delete()

    categories_with_subscriptions = Category.objects.annotate(
        user_subscribed=Exists(
            Subscription.objects.filter(
                user=request.user,
                category=OuterRef('pk'),
            )
        )
    ).order_by('name')
    return render(
        request,
        'subscriptions.html',
        {'categories': categories_with_subscriptions},
    )


# class IndexView(View):
#     def get(self, request):
#         printer.delay(10)
#         hello.delay()
#         return HttpResponse('Hello!')


class Index(View):
    def get(self, request):
        string = _('Hello World!')
        return HttpResponse(string)
