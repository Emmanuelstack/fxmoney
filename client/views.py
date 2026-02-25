from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.models import User  # username,email,password
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from .models import Customer,Transaction,Voucher


# authentication vs authorization 


# Create your views here.


def loginPage(request):
    error = None
    success = None
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST['password'] 
    
        if not email or len(email) < 3 :
            error = 'ensure you enter a valid email address'
            
        if not password :
            error = 'enter your password'   
            
        # authenticate then u login a user 
        user_found = authenticate(request, username=email, password= password)    
        
        if not user_found : 
            error = 'credentials not valid '
            
        else : 
            login(request, user_found)
            # now u can redirect 
            if request.GET.get("next"):
                return redirect(request.GET.get("next"))
            return redirect("client-home")
         
    return render(request,'login.html',{'error': error, 'success':success})
    
def logInnn(request) :
    html = '''
    <h2> LOGIN </h2>
    <form>
        <div>
            <label> Email </label>
            <input type="email">
        </div>
         <div>
            <label> Password </label>
            <input type="password">
        </div>
        
        <button type="submit"> login </button>
    
    </form>
    
    '''
    return HttpResponse(html)

    
def Signup(request):
    error = None 
    success = None 
    if request.method == "POST":
        email = request.POST.get('email')
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        
        if not email or len(email) < 3 :
           error = 'ensure you enter a valid email address'
           
        if password1 != password2 or len(password1) < 8 :
           error = 'password must both match and length of password must be at least 8 characters '
       
        try :
            User.objects.create_user(username=email, email=email, password=password1)
            success = 'user created successfully.... you can now login!'
        except Exception as e :  
            error = str(e)
           
    return render(request, 'signup.html', {"error" : error, "success": success})


def logoutUser(request):
    logout(request)
    return redirect("/login/")

@login_required(login_url='/login/')
def updateUserDetails(request:HttpRequest):
    success= None 
    Error = None 
    user = request.user
    if request.method == "POST":
        firstname = request.POST.get('firstname')
        lastname = request.POST['lastname']
        
        if len(firstname) < 2 or len(lastname) < 2 :
            error = 'specify your firstname or lastname properly with more than at least 2 characters'
        else :
            user.first_name =firstname
            user.last_name = lastname 
            user.save()
            success = 'user detail updated successfully'
    # user.first_name
    # user.last_name
    # user.save()
    return render(request,'update_detail.html',{'user': user})
    

# go design a dashboard page balance, transaction record, show account number 
# another page for transferring fund from one account number to another 
# another page for changing user pin and gender 
@login_required(login_url='/login/')
def pinView(request):
    if request.user.is_superuser :
        return redirect("admin")
    
    try : 
        # performing a read
        customer = Customer.objects.get(user=request.user)
        # help the frontend to know if the user has set pin b4 or not 
        pin_set_before = True if customer.pin else False 
        
        if request.method == 'POST' :
            # process the form request to update pin 
            new_pin : str = request.POST.get('new_pin')
            confirm_pin = request.POST['confirm_pin']
            
            if new_pin != confirm_pin or len(new_pin) != 4 or not new_pin.isdigit:
                return render(request,'pages/pin.html', {'customer':customer, 'pin_exist':pin_set_before,"error":"pin must be a four digit and must match with confirm pin"})
            
            
            if pin_set_before :
                # update 
                old_pin = request.POST.get('old_pin')
                old_pin_is_correct =customer.confirmIfUserPinIsCorrect(old_pin)
                if not old_pin_is_correct :
                    return render(request,'pages/pin.html', {'customer':customer, 'pin_exist':pin_set_before,"error":"your old pin is wrong"})
                else :
                    customer.hashUserPin(new_pin)
                    return render(request,'pages/pin.html', {'customer':customer, 'pin_exist':True,"success":"pin updated successfully"})  
                pass 
            else : 
                # setting up pin from scratch 
                customer.hashUserPin(new_pin)
                return render(request,'pages/pin.html', {'customer':customer, 'pin_exist':True,"success":"pin set successfully"})
                
        
        
        return render(request,'pages/pin.html', {'customer':customer, 'pin_exist':pin_set_before})
    
    except Exception as e : 
        return render(request, 'error.html', {"error": str(e)})

    
@login_required(login_url='/login/')
def dashboardPage(request:HttpRequest):
    if request.user.is_superuser :
        return redirect("admin")
    # crud 
    try : 
        # performing a read
        # customer = Customer.objects.get(user=request.user)
        customer, existed = Customer.objects.get_or_create(user=request.user)
        transactions = Transaction.objects.filter(sender = customer )
        
        print(f'User existed b4 : {existed}')
        return render(request,'pages/dashboard.html', {'customer':customer, 'transactions': transactions})
    
    except Exception as e : 
        return render(request, 'error.html', {"error": str(e)})

@login_required(login_url='/login/')
def depositPage(request):
    
    if request.method == 'POST':
        pin : str = request.POST.get('pin')
        voucher_code = request.POST['voucher_code']
        
        # confirm the user pin then check if the voucher exist and then if it exist check if the user requesting to load the voucher is the owner of the voucher
        try :
            customer = Customer.objects.get(user=request.user)
            pin_is_correct = customer.confirmIfUserPinIsCorrect(pin)
            if not pin_is_correct :
                return render(request,'pages/deposit.html', {'customer':customer,"error":"pin is wrong"})
            vouchers = Voucher.objects.filter(code=voucher_code)
            
            if len(vouchers) < 1 : 
                return render(request,'pages/deposit.html', {'customer':customer,"error":"voucher entered is wrong"})
            voucher = vouchers[0]
            if voucher.is_loaded :
               return render(request,'pages/deposit.html', {'customer':customer,"error":"voucher has already been loaded"})
            if voucher.customer != customer :
                return render(request,'pages/deposit.html', {'customer':customer,"error":"This voucher is not for you"})
            
            # success 
            customer.balance += voucher.amount
            customer.save()
            voucher.is_loaded = True 
            voucher.save()
            
            transaction = Transaction.objects.create(sender= customer,receiver = customer,amount= float(voucher.amount),transaction_type='deposit')
            transaction.save()
            
            # document the voucher Transaction and take them to the success page 
            return redirect(f"/success?tid={voucher.id}&amount={voucher.amount}&type=deposit")
        except Exception as e :
            return render(request, 'error.html', {'error':str(e)})
    return render(request, 'pages/deposit.html', {})

@login_required(login_url='/login/')
def searchAccountView(request):
    account_number = request.GET.get("account_number")
    if account_number : 
        # search from the Customer 
        try :
            customer = Customer.objects.get(account_number= account_number)
            same_user = True if request.user == customer.user else False
            return render(request,'pages/search.html', {'account_found' : True, 'customer': customer, "same_user":same_user})
        except Exception as e : 
            print(e)
            return render(request,'pages/search.html', {'account_found': False})
        
    return render(request,'pages/search.html', {})


@login_required(login_url='/login/')
def transferView(request):
    if request.method == 'POST':
        pin : str = request.POST.get('pin')
        amount = request.POST['amount']
        account_number = request.POST['account_number']
        
        # validate the amount that the sender has 
        try : 
            customer = Customer.objects.get(user=request.user)
            if customer.balance < float(amount) :
                return render(request,'pages/transfer.html', {'account_number':account_number, 'error':"insufficient fund"})
            if pin == None or pin == '' or len(pin) != 4 or not customer.confirmIfUserPinIsCorrect(pin) :
                return render(request,'pages/transfer.html', {'account_number':account_number, 'error':"incorrect pin"})
            reciever = Customer.objects.get(account_number = account_number)

            # proceed with transfer 
            reciever.balance += float(amount)
            customer.balance -= float(amount)
            
            reciever.save()
            customer.save()
            
            # document the transfer into Transaction
            transaction = Transaction.objects.create(sender= customer,receiver = reciever,amount= float(amount),transaction_type='transfer')
            transaction.save()
            return redirect(f"/success?tid={transaction.id}&amount={amount}&type=transfer")
        except Customer.DoesNotExist :
            return render(request,'pages/transfer.html', {'account_number':account_number, 'error':'Account number not valid'})
        except Exception as e : 
            print(e)
            return render(request,'pages/transfer.html', {'account_number':account_number, 'error':str(e)})
        
    account_number = request.GET.get("account_number") 
    return render(request,'pages/transfer.html', {'account_number':account_number})




@login_required(login_url='/login/')
def paymentSuccessView(request):
    transaction_id = request.GET.get("tid")
    amount= request.GET.get("amount")
    transaction_type= request.GET.get("type")
    return render(request,'pages/success.html', {'transaction_id':transaction_id, "amount":amount, 'transaction_type':transaction_type})

@login_required(login_url='/login/')
def transactionHistory(request):
    customer = Customer.objects.get(user = request.user)
    transactions = Transaction.objects.filter(sender = customer )
    return render(request, 'pages/transaction.html', {'transactions': transactions})


def dynamicTesting(request, id):
    return render(request,'dynamic.html', { "id":id})