import cgi
import datetime
import urllib
import webapp2
import time

from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import users


class GroceryItem(ndb.Model):
    name = ndb.StringProperty()
    cost = ndb.FloatProperty()
    num  = ndb.IntegerProperty() 
    avatar = ndb.BlobProperty()
    datetime = ndb.DateTimeProperty(auto_now_add=True)
    user = ndb.UserProperty(auto_current_user_add=True)


def make_it_money(number):
    """
    always:
    - shows 2 decimal places
    - shows thousands separator if necessary
    - retains integrity of original var for later re-use
    - allows for concise calling
    from http://stackoverflow.com/questions/15658925/universal-method-for-working-with-currency-with-no-rounding-two-decimal-places
    """
    import math
    return '$' + str(format(math.floor(number * 100) / 100, ',.2f'))


class MainPage(webapp2.RequestHandler):
    def get(self):
        # Checks for active Google account session
        self.response.headers['Content-Type'] = 'text/html'
        user = users.get_current_user()

        self.response.out.write('<html><body><h1>UVa CS4740 Spring 2015 Grocery Buddy</h1><p>A service by Mitchell Smith</p>')
        if self.request.get("notimage"):
            self.response.out.write("Please enter a valid image")

        if user:
            self.response.write('<h2>Grocery list for %s</h2>' % (user.nickname()))

            print "Grocery items"
            grocery_items_query = GroceryItem.query(GroceryItem.user==user)
            grocery_items = grocery_items_query.fetch()
            print grocery_items

            if len(grocery_items) > 0:
                total = 0.00
                self.response.out.write(""" 
                        <table border="1" style="width:60%">
                        <tr>
                            <th>Picture</th>
                            <th>Time added</th>
                            <th>Name</th>
                            <th>Cost per item</th>
                            <th>Number</th>
                            <th>Total</th>
                        </tr>
                        """)
                for item in grocery_items:
                    total += item.cost * item.num
                    self.response.out.write("""
                        <tr>
                            <td><img src="/img?img_id=%s"></td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                        </tr>
                        """ % (item.key.urlsafe(), item.datetime, item.name,  make_it_money(item.cost), item.num, make_it_money( item.cost * item.num)))
                self.response.out.write("</table>")
                self.response.out.write("<p>Total: %s</p>"%(make_it_money(total)))
                self.response.out.write("""
                        <form action="/clear" method="post">
                            <div><input type="submit" value="Clear all items"></div>
                        </form>
                        """)
            else:
                self.response.out.write("<br>No groceries<br>")

            self.response.out.write("""
                        <h2>Add groceries</h2>
                  <form action="/upload" enctype="multipart/form-data" method="post">
                    <div><label>Picture:</label></div>
                    <div><input type="file" name="img" required/></div>

                    <div><label>Name:</label></div>
                    <div><input type="text" name="name" required/></div>
                    
                    <div><label>Cost per item(in dollars):</label></div>
                    <div><input type="number" min="0.01" step = "0.01" name="cost" /></div>
                    
                    <div><label>How many:</label></div>
                    <div><input type="number" min=1 name="num" required/></div>
                    <div><input type="submit" value="Add Grocery Item"></div>
                  </form>
                  <hr>
                </body>
              </html>""" )
            self.response.out.write('<div><a href="/login">Logout</a></div>')
        else:
            self.response.out.write('<div><a href="/login">Login</a></div>')
        


class Image(webapp2.RequestHandler):
    def get(self):
        print "getting image"
        groceryitem = ndb.Key(urlsafe=self.request.get('img_id')).get()
        if groceryitem.avatar:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(groceryitem.avatar)
        else:
            self.response.out.write('No image')


class Clear(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            grocery_items_query = GroceryItem.query(GroceryItem.user==user)
            grocery_items = grocery_items_query.fetch(keys_only=True)
            ndb.delete_multi(grocery_items)
            time.sleep(1)
        self.redirect('/')

class Upload(webapp2.RequestHandler):
    def post(self):

        user = users.get_current_user()
        if user:
            groceryitem = GroceryItem()
            try:
                avatar = images.resize(self.request.get('img'), 32, 32)
            except images.NotImageError:
                self.redirect('/?notimage=true')
                return

            groceryitem.avatar = avatar
            groceryitem.name = self.request.get('name')
            groceryitem.cost = float(self.request.get('cost'))
            groceryitem.num = int(self.request.get('num'))
            groceryitem.put()
            # used to let queries finish
            time.sleep(1)
        self.redirect('/')

class Login(webapp2.RequestHandler):
    def get(self):
        # Checks for active Google account session
        user = users.get_current_user()

        if user:
            self.redirect(users.create_logout_url("/"))
        else:
            self.redirect(users.create_login_url("/"))

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/login', Login),
                               ('/upload', Upload),
                               ('/clear', Clear),
                               ('/img', Image),],
                               debug=True)
