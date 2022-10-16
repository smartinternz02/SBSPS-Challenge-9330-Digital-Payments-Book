# AmendsPro
## About: 
- This application is a part of the submission made for IBM Back Challenge 2022. 
- AmendsPro is a digital payments book app with an integrated payment gateway to help small business and others get their business up and running online with ease. 
- The app is designed in a way that it can be customized for different business based on their business model, for example Grocery stores can sell Groceries through the Products section and Book stores can sell books etc.
- Every store has some kind of Billing system and in order to take things online we have to integrate online payment gateways of some sort and then from there we have to manually keep track of Dues and Partial Payments in order to alert users/customers of that particular store. This is quite a tedious task, which is exactly why we came up with an All in one integrated idea. 
- Combining a ecommerce system with a Digital Payment Book concept opens the door for more opportunities for both the customer and the user, Hence the application.

## Execution:
- Once the repo is cloned or downloaded, move to the respective folder and 
- run `docker image build -t my_flaskapp`
- run `docker run (image name)`

## Working: 
1. Dashboard: 
     - *NavBar*: Contains links to different parts of the application.
     - *Infobar*: Contains links to the Compare section and provides quick insight into the Recent Payments and a quick overview of Analysis for this month.
     - *Main Section*: Provides information about the upcoming dues, Brief Monthly Comparison and Frequently bought items.

2. Payments:
     - *Payments(Dues)*: Provides information about the partial payments, in other words the dues that you have to clear off.
     - *History*: Provides information about the transaction history that you've made so far.

3. Analysis (Compare):
    - Provides a quick comparison of the expenses of the selected two months. 
    - Details about the Budgets, Total Expense and most profitable month etc are mentioned here.

4. Products:
     - This is the section that will be customized based on the store the application is integrated to.
     - From here, users can add items to the cart and make hassle free checkouts.

5. Cart:
     - *Save List*: Save your current cart items as a Shopping list to help save time having to add the same items over and over again every month.
     - *Partial Checkout*: Make purchase in two halves, first half to be paid initially and the second half can be paid next month.
     - *Checkout*: Normal checkout option that lets you purchase without debts.

6. Profile: 
     - *User Details*
     - *Budget Details*: contains information about the budget for the current month and how much you've spent so far.
     - *Pinned Lists*: Contains details about the shopping lists you've created so far using the Save List option from the Cart section.
