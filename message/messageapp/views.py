from django.shortcuts import render,HttpResponse,redirect
from messageapp.models import Message
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from messageapp.models import Product, Cart, Order
from django.db.models import Q
import random
import razorpay

# Create your views here.
def home(request):
    context={}
    p=Product.objects.filter(is_active=True)  
    context['products']=p
    print(p)
    
    #userid=request.user.id
    #print("id of logged in user",userid)
    #print("Result",request.user.is_authenticated) #this is boolean function
    return render(request,'index.html',context)

def about(request):
    return render(request,'about.html')

def product_details(request,pid):
    context={}
    context['products']=Product.objects.filter(id=pid)
    return render(request,'product_details.html',context)

def contact(request):
    return render(request,'contact.html')

def cart(request):
    return render(request,'cart.html')

def register(request):
    context={}
    if request.method=="POST":
        uname=request.POST['uname']
        upass=request.POST['upass']
        ucpass=request.POST['ucpass']
        if uname=="" or upass=="" or ucpass=="":
            context['Errormsg']="Field cannot be empty"
            return render(request,'register.html',context)
        elif upass!=ucpass:
            context['Errormsg']="Passwoard did not match"
            return render(request,'register.html',context)
                       
        else:
            try:
                u=User.objects.create(username=uname,password=upass,email=uname)
                u.set_password(upass)
                u.save()
                context['Success']="User added successfully"
                return HttpResponse("User added successfully")
            except Exception:
                context['Errormsg']="Username already exits"
                return render(request,'register.html',context)
                             
    else:
        return render(request,'register.html')
    #return render(request,'register.html')

def user_login(request):
    context={}
    if request.method=="POST":
        uname=request.POST['uname']
        upass=request.POST['upass']
        if uname=="" or upass=="":
            context['Errormsg']="Field cannot be empty"
            return render(request,'login.html',context)
        
        else:
            u=authenticate(username=uname,password=upass) # is work as select qurey...when user name password not match is written none 
            if u is not None :
                login(request,u)
                return redirect('/home')
            else:
                context['Errormsg']="Invalid username and password"
                return render(request,'login.html',context)
    else:
        return render(request,'login.html')

def user_logout(request):
    logout(request)
    return redirect("/home") 

def catfilter(request,cv):
    q1=Q(is_active=True)  #if an apply more than condition it can apply
    q2=Q(cat=cv) 
    p=Product.objects.filter(q1 & q2)
    print(p)
    context={}
    context['products']=p 
    return render(request,'index.html',context)

def sort(request,sv):
    if sv=='0':
        col='price'
    else:
        col='-price'
        
    p=Product.objects.filter(is_active=True).order_by(col)
    context={}
    context['products']=p
    return render(request,'index.html',context)

def range(request):
    min=request.GET['min']
    max=request.GET['max']
    q1=Q(price__gte=min)
    q2=Q(price__lte=max)
    q3=Q(is_active=True)
    p=Product.objects.filter(q1 & q2 & q3)
    context={}
    context['products']=p
    return render(request,'index.html',context)


def addtocart(request,pid):
    if request.user.is_authenticated:
        userid=request.user.id 
        u=User.objects.filter(id=userid)
        print(u[0])
        p=Product.objects.filter(id=pid)
        print(p[0])
        c=Cart.objects.create(uid=u[0],pid=p[0])
        c.save()
        return HttpResponse("Product added to cart")
        #print(pid)
        #print(userid)
        #return HttpResponse("id feched")
    else:
        return redirect('/user_login')
           
def remove(request,cid): 
    c=Cart.objects.filter(id=cid)  
    c.delete()
    return redirect('/viewcart')

def viewcart(request):
    userid=request.user.id 
    c=Cart.objects.filter(uid=userid)
    s=0
    np=len(c) #all products avilable in c
    for x in c :
        #print(x)
        #print(x.pid.price)
        s=s+x.pid.price*x.qty #0+18000
        
    context={}
    context['products']=c
    context['n']=np #n is a key
    context['total']=s
    return render(request,'cart.html',context)


def updateqty(request,qv,cid): # qv is variable
    #print(type(qv)) #check the type 'str'
    c=Cart.objects.filter(id=cid)
    #print(c[0])
    #print(c[0].qty)
    #return HttpResponse("qty fetched")
    if qv=='1':
        t=c[0].qty+1
        c.update(qty=t)
    else :
        if c[0].qty>1:
            t=c[0].qty-1
            c.update(qty=t)
    return redirect('/viewcart')

def placeorder(request):
    userid=request.user.id 
    c=Cart.objects.filter(uid=userid)
    oid=random.randrange(1000,9999) #oid=orderid
    print("Order id is :",oid)
    for x in c :
        #print(x)
        #print("Product id is :",x.pid)
        #print("User id is :",x.uid)
        #print("qty is :",x.qty)
    #return HttpResponse("In placeorder")
        o=Order.objects.create(order_id=oid,pid=x.pid,uid=x.uid,qty=x.qty)
        o.save()
        x.delete()
    orders=Order.objects.filter(uid=request.user.id)
    s=0
    np=len(orders) #all products avilable in c
    for x in orders :
        #print(x)
        #print(x.pid.price)
        s=s+x.pid.price*x.qty #0+18000
        
        context={}
        context['products']=orders
        context['n']=np #n is a key
        context['total']=s
    return render(request,'place_order.html',context)    




def makepayment(request):  
    orders=Order.objects.filter(uid=request.user.id)
    s=0
    for x in orders :
        s=s+x.pid.price*x.qty
        oid=x.order_id
    
    client = razorpay.Client(auth=("rzp_test_hQgWhgaZPqh6WZ", "jaMnhtm7RsRRFF0xt7uN4q50"))
    data = { "amount": s*100, "currency": "INR", "receipt": oid }
    payment = client.order.create(data=data)
    print(payment)
    context={}
    context['data']=payment
    return render(request,'pay.html',context)


        
        
            
        
    


# login(request):
    #return render(request,'login.html')


def testing(request):
    return HttpResponse("Hello linked successfully")


#def create(request):
    print('request is: ',request.method)
    return render(request,'create.html')

def create(request):
       print("Method is",request.method)
       if request.method =="GET":
              return render(request,'create.html')
       else:
            #return HttpResponse("insert data into DB")
            a=request.POST['uname']
            b=request.POST['umail']
            c=request.POST['unum']
            d=request.POST['msg']
            print("Name is :",a)
            print("Email is :",b)
            print("Mobile is :",c)
            print("Message is :",d)
            x=Message.objects.create(name=a,email=b,mobile=c,msg=d)
            x.save()
            return redirect('/dashboard')
            #return HttpResponse("Values fetched successfully")
            
def dashboard(request):
    m=Message.objects.all()
    context={}
    context["data"]=m
    #print(m)
    return render(request,'dashboard.html',context)
    #return HttpResponces("Data fetch from the db ")  # print on browser
            
def edit(request,rid):
    if request.method=="GET":
    #print("Id to be edited is :")
        m=Message.objects.filter(id=rid)
        print(m)
        context={}
        context["data"]=m
        return render(request,'edit.html',context)
    else:
        un=request.POST['uname']
        umail=request.POST['umail']
        unum=request.POST['unum']
        umsg=request.POST['msg']
        m=Message.objects.filter(id=rid)
        m.update(name=un,mobile=unum,email=umail,message=umsg)
        return redirect('/dashboard')
    #return HttpResponce("ID to be edited is:"+rid)
    
    
def delete(request,rid):
    #print("ID to be deleted is:"+rid)
    m=Message.objects.filter(id=rid)
    print(m)
    m.delete()
    return redirect('/dashboard')
    #return HttpResponse("ID to be deleted is:"+rid)
    
        


    