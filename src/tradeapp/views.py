from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from .binance_app import BinanceApp
from .forms import AlgorithmForm
from .models import Algorithm
from .models import Order


class ManageView(View):
    def __init__(self, **kwargs):
        self.b_app = BinanceApp()
        super().__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        context = {}

        form = AlgorithmForm(None)
        if request.POST.get('command') == 'Delete':
            query = Algorithm.objects.get(pk=request.POST.get('primary_key'))
            if not query.active:
                query.delete()
            else:
                url = ''
                resp_body = '<script>alert("DO NOT TRY TO DELETE THE ACTIVE MODEL");\
                                 window.location="%s"</script>' % url
                return HttpResponse(resp_body)
        elif request.POST.get('command') == 'Create':
            form = AlgorithmForm(request.POST or None)
            if form.is_valid():
                form.save()
        elif request.POST.get('command') == 'SetActive':
            active_model = Algorithm.objects.get(pk=request.POST.get('primary_key'))
            active_model.active = True
            active_model.save()
            self.b_app.load_active_model()

        context['form'] = form
        context['algorithms'] = Algorithm.objects.all().order_by('-name')
        return render(request, "manage.html", context)

    def get(self, request, *args, **kwargs):
        self.b_app.stop_algorithm()
        context = {}
        form = AlgorithmForm(None)
        context['form'] = form
        context['algorithms'] = Algorithm.objects.all().order_by('-name')
        return render(request, "manage.html", context)


class HomeView(View):

    def __init__(self, **kwargs):
        self.b_app = BinanceApp()
        super().__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        # we use ajax to avoid the need to re render our template when exchanging data
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            if request.POST.get('command') == "start":
                if self.b_app.start_algorithm():
                    response = {'msg': "Algorithm started"}
                else:
                    response = {'msg': "Algorithm already running"}
                return JsonResponse(response)

            elif request.POST.get('command') == "stop":
                if self.b_app.stop_algorithm():
                    response = {'msg': "Algorithm stopped"}
                else:
                    response = {'msg': "Algorithm already stopped"}
                return JsonResponse(response)

        else:
            response = {'msg': "Unknown Post request"}
            return JsonResponse(response)

    def get(self, request, *args, **kwargs):
        # we use ajax to avoid the need to re render our template when exchanging data
        context = {}
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            if request.GET.get('command') == "get_logs":
                context['logs'] = self.b_app.get_algorithm_logs()
                return JsonResponse(context)
            else:
                context['account'] = self.b_app.get_account_data()
                return JsonResponse(context)
        else:
            context['orders'] = Order.objects.filter(algorithm=self.b_app.active_model).order_by('-time')
            context['algorithm'] = model_to_dict(self.b_app.active_model)
            return render(request, 'home.html', context)
