# Family Budget Web App AKA SquirrelStack

_Pile Up Your Prosperity_

SquirrelStack is your companion in the journey towards financial stability and growing wealth. Our app allows families and individuals to seamlessly manage their income, expenses, and savings, ensuring that every penny is accounted for. With a blend of user-friendly interface and powerful financial tools, it ensures that managing your budget becomes as simple and efficient as possible. Dive into a robust suite of features that bring clarity to your financial status and help you plan for a prosperous future.

## Overview

Family Budget is a web-based application developed with Flask, aimed to manage family budgets and savings in an easy and intuitive manner. With a robust saving project management, monthly savings tracking, and tags management features, Family Budget provides a seamless user experience for handling various financial aspects.

## ⚠️ Warning: Project Under Testing ⚠️

This project is currently under testing and might contain bugs or lack some functionalities. Users and developers are invited to report any issues or unexpected behaviors.

## Features

### [Home](/)
A landing page that provides a monthly summarization.
- **Add Expense**: Functionalities to insert new Expenses.
- **Add Incomes**: Functionalities to insert new Income.

### [Manage Tags](/tags)
Facilitate the creation, visualization, and deletion of tags, which can be associated with various financial entries. Users can:
- **Create Tags**: Form to add new tags.
- **View & Delete Tags**: A comprehensive list of all created tags along with the option to delete them.

### [Savings](/savings)
Page dedicated to managing and viewing savings for the current month. It offers:
- **Add Savings**: Functionalities to insert new savings data.
- **View Savings**: See all your saving instances for the current month.
- **Delete Savings**: Option to delete specific savings records.

### [Monthly Summary](/summary_month)
Provides a summarized view of all the transactions and savings occurring in a particular month. Display relevant financial data and summaries.

### [Yearly Summary](/summary_year)
Overview of the financial data, savings, and expenses on an annual basis, providing insights into the overall yearly financial performance.

### [All Entries](/all)
Displays a comprehensive view of all financial entries. Provides a clear tabulated view of every transaction, saving, and expense recorded in the system.

### [Data Mining](/data_mining)
An advanced feature that may encompass various data analytics and visualization functionalities, offering deeper insights into user’s financial data.

### [Future Movements](/future_expenses)
Track and manage your future planned expenses and incomes. Organize and visualize all the planned future financial movements and their impact on your budget.

### [Savings Project](/savings_projects)
Manage and monitor saving projects by:
- **Creating Projects**: Initiating new savings projects by defining the essential details.
- **Viewing Projects**: Observing ongoing projects and their related data.
- **Monthly Deadlines Management**

### [Forecast](/forecast)
Predictive feature providing financial forecasts based on the existing data and trends. Offers insights into potential future financial statuses.

## Installation & Usage

### Local Installation

#### Prerequisites

- **Python**: Ensure that you have Python 3.10 or newer installed.
- **Pip**: Make sure that the Python package installer is available.

#### Steps

1. **Clone the Repository:**
    ```sh
    git clone https://github.com/mikeleord/SquirrelStack.git
    cd SquirrelStack
    ```
   
2. **Install Dependencies:**
    Use pip to install all the necessary packages.
    ```sh
    pip install -r requirements.txt
    ```

3. **Run the Application with Flask:**
    You can start the application using Flask.
    ```sh
    flask run
    ```
    Now, access the application on `http://127.0.0.1:5000/` in your web browser.

4. **Run the Application with gunicorn:**
    You can start the application using Flask.
    ```sh
    gunicorn -b 0.0.0.0:8000 app:app
    ```
    Now, access the application on `http://127.0.0.1:8000/` in your web browser.

### Installation with Docker

#### Prerequisites

- **Docker**: Ensure Docker is installed and running on your system.

#### Steps
  
**Run the Docker Container:** Run a container using your Docker image.
```sh
docker run -d -p 8000:8000  --name squirrelstack --restart=always -v /path/on/host:/app/db squirrelstack:beta1
```
or with volume:
```sh
docker volume create squirrelstack_data
docker run -d -p 8000:8000 -v squirrelstack_data:/app squirrelstack:beta1
```
If you are using Docker Compose, ensure your services are defined in a `docker-compose.yml` and start them with:
example docker-compose.yml

```yaml
version: '3.8'

services:
  your-service-name:
    image: squirrelstack:beta1
    ports:
      - "8000:8000"
    volumes:
      - /path/on/host:/app/db
```
```sh
    docker-compose up
```

Visit `http://127.0.0.1:8000/` in your web browser to access the application.

## Creating a Password with Flask-HTPasswd

This application uses Basic Auth for simple authentication. To set up your own username and password, you can utilize `flask-htpasswd`.

### Prerequisites
- **HTPasswd**: Ensure you have `apache2-utils` installed. If not, install it using pip:
```shell
sudo apt install apache2-utils
htpasswd -c /path/to/.htpasswd my_username
```
for more details visit: [ flask-htpasswd 0.5.0 ](https://pypi.org/project/flask-htpasswd/)

for docker:
```shell
docker exec -it [container id] /bin/bash "htpasswd /app/.htpasswd [my_username]"
docker restart [container id]
```
or add manually in .htpasswd

## Contributing

This project is open for contributions. Here are a few ways you can help:
- **Report Bugs**: If you encounter any issues or unexpected behaviors, please file a bug report in the GitHub issue tracker.
- **Feature Requests**: If you have ideas for new features or improvements, feel free to create an issue describing your suggestion.
- **Pull Requests**: If you've implemented a new feature or fixed a bug, please feel free to open a pull request!


## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) file for details.

---

**Note**: Feel free to personalize and extend this README template according to the specificities of your project. Ensure to keep it updated as your project evolves to help new users or contributors understand the purpose and functionality of your application.

more detail: https://github.com/mikeleord/SquirrelStack