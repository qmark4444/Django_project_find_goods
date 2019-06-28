'''
Created on Oct 9, 2017

@author: LongQuan
'''
from django.http import HttpResponse
from django.shortcuts import render, redirect
from operator import itemgetter
from django.db import connections
import json
import urllib.request
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import login, authenticate, logout
from .forms import SignUpForm
from .models import AppUser
import re

class Distance:
    def __init__(self, api_key):
        self.api_key = api_key   #set google map api key
        self.origins = []
        self.destinations = []
        self.origin = ''

    def set_origins(self, origin_loc):
        self.origins.append(origin_loc)
        
    def setOrigin(self, origin_loc):
        self.origin = origin_loc

    def set_destinations(self, dest_loc):
        self.destinations.append(dest_loc)

    def computeDistance(self):
        base_url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'
        payload = {
            #'origins' : '|'.join(self.origins),
            'origins' : self.origin,
            'destinations' : '|'.join(self.destinations), 
            'mode' : 'driving',
            'api_key' : self.api_key
        } 
        target_url = base_url \
                    + 'origins=' + payload['origins'] \
                    +'&destinations=' + payload['destinations'] \
                    + '&key=' + payload['api_key']
        req = urllib.request.Request(target_url)
        results = [] # a string list containing all distances
        try:    
            response = urllib.request.urlopen(req) # HTTPResponse from the HTTPRequest
        except urllib.error.HTTPError as e:     
            print('Error in accessing Google maps URL: status code is ' + str(e.code))
        else:
            try: # Try/catch block should capture the problems when loading JSON data
                #if response is valid JSON-encoded data, we can directly use
                x = json.load(response)
 
                # put distance of each origin/destination into results
                for isrc, src in enumerate(x['origin_addresses']):
                    for idst, dst in enumerate(x['destination_addresses']):
                        row = x['rows'][isrc]
                        cell = row['elements'][idst]
                        if cell['status'] == 'OK':
                            results.append(cell['distance']['text'])
                        else:
                            print('{} to {}: status = {}'.format(src, dst, cell['status']))
            # TODO Or in a database,
            except ValueError:
                print('Error while parsing JSON response, program terminated.')
        return results
    
def addressConvertion(address):
    #replace everything after streetnumber and streetname with Ottawa,ON
    streetList = address[:address.index(',')].strip().split(' ')
    city = 'Ottawa'
    province = 'ON'
    gMapAddress = ''
    for st in streetList:
        gMapAddress += st + '+'
    gMapAddress += city + '+' + province
    return gMapAddress

def getContents(cursor, row, locationDistances, contents):
    while row is not None:  
        row_dict = {}
        row_dict['prodNum'] = row[0]
        row_dict['name'] = row[1]
        row_dict['brand'] = row[2]
        row_dict['info'] = row[3]
        row_dict['price'] = str(row[4])
        row_dict['store'] = row[5]
        row_dict['store_location'] = row[6]
        row_dict['weight'] = str(row[7])#row[7]
        row_dict['volumn'] = str(row[8])
        row_dict['package'] = row[9]
        row_dict['unit_price'] = str(row[10])
        row_dict['country_origin'] = row[11]
        row_dict['distance'] = locationDistances[row[6]]
        contents.append(row_dict)
        row = cursor.fetchone()
    return 
    
def dbConnect():
    return connections['foodengineDB']

myMapDistance = Distance('AIzaSyCLZ3Fv8hRI-1yOQu4xqVvyqlSqz6ctt80') #global object for re-use

def home(request):
    # when first time load, clear all session
    for key in list(request.session.keys()):
        del request.session[key]
    
    context_dict = {}
    # when load, check database table and get all brands and countries for Filter, and calculate distances
    brandCounts = {} #HashMap to quickly get unique brand names
    countryCounts = {}
    userAddr = '1385 Woodroffe Ave, Nepean, ON' # current location: when first time loading (no post code)
    request.session['currentLocation'] = userAddr
    origin = addressConvertion(userAddr)
    myMapDistance.setOrigin(origin)
    locations = []
    db_table = "Product"
    cursor = dbConnect().cursor()
    cursor.execute("select * from " + db_table) 
    row = cursor.fetchone()
    while row is not None:  
        #get unique brands
        if row[2] not in brandCounts:
            brandCounts[row[2]] = 1
        else:
            brandCounts[row[2]] += 1
        #get unique countries
        if row[11] not in countryCounts:
            countryCounts[row[11]] = 1
        else:
            countryCounts[row[11]] += 1
        #get unique locations
        if row[6] not in locations:
            destin = addressConvertion(row[6])
            myMapDistance.set_destinations(destin)
            locations.append(row[6]) 
        row = cursor.fetchone()        
    # close cursor
    cursor.close()
    #calculate all distances
    distances = myMapDistance.computeDistance()
    if len(distances) == 0: # If Google map api stops working
        distances = len(locations)*['NA']
    request.session['locationDistances'] = dict(zip(locations, distances))
    request.session['brandCounts'] = brandCounts
    request.session['countryCounts'] = countryCounts
    context_dict['searchQuery'] = request.session.get('searchQuery')
    return render(request, 'foodengine/app_home.html', context_dict)

def userHome(request, uid):
    context_dict = {}
    context_dict['searchQuery'] = request.session.get('searchQuery')
    context_dict['userID'] = uid
    return render(request, 'foodengine/app_home.html', context_dict)

def search(request):
    context_dict = {}
    context_dict['currentLocation'] = request.session.get('currentLocation')
    context_dict['searchQuery'] = request.session.get('searchQuery')
    productName = request.GET.get('product_name')
    #if query is None, stay here
    if len(productName) is 0:
        return render(request, 'foodengine/app_home.html')
    cursor = dbConnect().cursor()
    db_table = "Product"
    db_column = "prodName"
    cursor.execute("select * from " + db_table + " where " + db_column + " LIKE %s", ("%"+productName+"%",)) 
    row = cursor.fetchone()    
    products = []
    context_dict['products'] = products
    locationDistances = request.session.get('locationDistances')
    getContents(cursor, row, locationDistances, products)     
    # close cursor
    cursor.close()
    request.session['search_result'] = products #static
    request.session['filter_search_result'] = products #dynamic
    request.session['searchQuery'] = {'prodName': productName}
    context_dict['allBrands'] = request.session.get('brandCounts').keys()
    context_dict['allCountries'] = request.session.get('countryCounts').keys()
    return render(request, 'foodengine/result.html', context_dict)

def refineSearch(request):
    context_dict = {}
    context_dict['allBrands'] = request.session.get('brandCounts').keys()
    context_dict['allCountries'] = request.session.get('countryCounts').keys()
    context_dict['currentLocation'] = request.session.get('currentLocation')
    context_dict['searchQuery'] = request.session.get('searchQuery')
    brand = request.GET.get('brand')
    country = request.GET.get('country')
    productName = request.GET.get('product_name')
    request.session['filter'] = {'brand': brand, 'country': country, 'prodName': productName}
    context_dict['filter'] = request.session['filter']
    context_dict['products'] = request.session.get('filter_search_result')
    locationDistances = request.session.get('locationDistances')
    if len(brand) is 0 and len(country) is 0 and len(productName) is 0:
        return render(request, 'foodengine/result.html', context_dict)
    db_table = "Product"
    sqlstmt = "select * from " + db_table
    if not len(brand) is 0:
        try: #if string contains ' character
            brand.index("'") #if ' exists it won't raise exception
            brand = re.sub("'","\\'", brand)
        except:
            pass
        sqlstmt +=  " where brand = " + "'"+brand+"'"
    else:
        sqlstmt +=  " where brand REGEXP '.*'"
    if len(country) is not 0:
        try: #if string contains ' character
            country.index("'") #if ' exists it won't raise exception
            country = re.sub("'","\\'", country)
        except:
            pass
        sqlstmt += " and country = " + "'"+country+"'"
    else:
        sqlstmt += " and country REGEXP '.*'"
    if len(productName) is not 0:
        try: #if string contains ' character
            productName.index("'") #if ' exists it won't raise exception
            productName = re.sub("'","\\'", productName)
        except:
            pass
        sqlstmt += " and prodName LIKE " + "'%"+productName+"%'"
    else:
        sqlstmt += " and prodName REGEXP '.*'" 
    cursor = dbConnect().cursor()
    cursor.execute(sqlstmt) 
    row = cursor.fetchone()    
    products = []
    context_dict['products'] = products
    getContents(cursor, row, locationDistances, products)     
    # close cursor
    cursor.close()
    request.session['filter_search_result'] = products #dynamic
    return render(request, 'foodengine/result.html', context_dict)

def changeLocation(request):
    context_dict = {}
    context_dict['allBrands'] = request.session.get('brandCounts').keys()
    context_dict['allCountries'] = request.session.get('countryCounts').keys()
    context_dict['currentLocation'] = request.session.get('currentLocation')
    context_dict['searchQuery'] = request.session.get('searchQuery')
    context_dict['filter'] = request.session.get('filter')
    context_dict['products'] = request.session.get('filter_search_result')
    locationDistances = request.session.get('locationDistances')
    locations = locationDistances.keys()
    if request.method == 'POST':
        userAddr = request.POST.get('new_location')
        request.session['currentLocation'] = userAddr
        context_dict['currentLocation'] = userAddr
        origin = addressConvertion(userAddr)
        myMapDistance.setOrigin(origin)
        distances = myMapDistance.computeDistance()
        if len(distances) == 0: # If Google map api stops working
            distances = len(locations)*['NA']
        request.session['locationDistances'] = dict(zip(locations, distances))
    return render(request, 'foodengine/result.html', context_dict)

def sort(request):
    context_dict = {}
    sort = request.GET.get('sort').split('%')
    sort_by = sort[0].split(' ')[1]
    order_by = sort[1].split(' ')[1]
    sharedContext = request.session.get('filter_search_result')
    if(sort_by != None):
        if order_by == 'desc':
            context_dict['products'] = sorted(sharedContext, key=itemgetter(sort_by), reverse=True)
        else:
            context_dict['products'] = sorted(sharedContext, key=itemgetter(sort_by))
    context_dict['currentLocation'] = request.session.get('currentLocation')
    context_dict['searchQuery'] = request.session.get('searchQuery')
    context_dict['allBrands'] = request.session.get('brandCounts').keys()
    context_dict['allCountries'] = request.session.get('countryCounts').keys()    
    context_dict['filter'] = request.session.get('filter')
    return render(request, 'foodengine/result.html', context_dict)

def equals(standard, x):
    if standard == None or standard == '' or standard == x:
        return True
    return False

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'foodengine/sign_up.html', {'form': form})

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return render(request, 'foodengine/app_home.html', {'user': user})
            else:
                return render(request, 'foodengine/app_home.html', {'signin_message': "Your account is disabled."})
        else:
            return render(request, 'foodengine/sign_in.html', {'signin_message': "Invalid login details supplied."})
    return render(request, 'foodengine/sign_in.html')

def signout(request):
    logout(request) # use django.contrib.auth logout
    return HttpResponseRedirect(reverse('home', args=()))

def userProfile(request, uid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))
    locationDistances = request.session.get('locationDistances')
    context_dict = {}
    context_dict['favorites'] = getFavorites(uid, locationDistances)
    return render(request, 'foodengine/user_profile.html', context_dict)

def upgradeUser(request, user_id):#upgrade user to prime member
    user = AppUser.objects.get(pk=user_id)
    user.member = 'Y'
    user.save()
    return render(request, 'foodengine/user_profile.html', {'user': user})

def member(request):
    if not request.user.isMember:
        return render(request, 'foodengine/user_profile.html')
    return render(request, 'foodengine/member.html')

def about(request):
    return HttpResponse('this is about Food Engine')

def saveFavorites(request):
    context_dict = {}
    context_dict['allBrands'] = request.session.get('brandCounts').keys()
    context_dict['allCountries'] = request.session.get('countryCounts').keys()
    context_dict['currentLocation'] = request.session.get('currentLocation')
    context_dict['filter'] = request.session.get('filter')
    context_dict['products'] = request.session.get('filter_search_result')
    favoriteProducts = context_dict['products']
    UID = request.GET.get('save')
    try:
        db = dbConnect()
        cursor = db.cursor()
        #first delete all records with this userID
        if cursor.execute("SELECT count(*) FROM Favorites") is not 0:
            cursor.execute("DELETE FROM Favorites WHERE userID=" + UID)
        for product in favoriteProducts:
            sqlstmt = "INSERT INTO Favorites (userID, pNum) VALUES ('%s', '%s')" 
            userID = UID
            pNum = product['prodNum']
            cursor.execute(sqlstmt % (userID, pNum))
        db.commit()
    except IOError:
        #if database connection error, give a message
        context_dict['saveFavorite_message'] = "Error happens when saving favorites"
    # close cursor
    cursor.close() 
    context_dict['saveFavorite_message'] = "You just saved your favorite products"
    return render(request, 'foodengine/result.html', context_dict)

def getFavorites(uid, locationDistances): 
    context_dict = {}
    favoriteProducts = []
    try:
        db = dbConnect()
        cursor = db.cursor()
        cursor.execute("select * from Product join Favorites" \
                       + " on Favorites.userID =" + uid \
                      + " and Favorites.pNum = Product.prodNum") 
        row = cursor.fetchone()
        if row is None:
            context_dict['retrieveFavorite_message'] = "No favorite product saved yet"
        else: 
            getContents(cursor, row, locationDistances, favoriteProducts)    
        # close cursor
        cursor.close()
    except IOError:
        #if database connection error, give a message
        context_dict['retrieveFavorite_message'] = "Error happens when retrieving favorites"
    # close cursor
    cursor.close() 
    context_dict['favorites'] = favoriteProducts
    return favoriteProducts