#This file is part of Family Budget Web App AKA SquirrelStack.
#Family Budget Web App AKA SquirrelStack is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#Family Budget Web App AKA SquirrelStack is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU General Public License
#along with Family Budget Web App AKA SquirrelStack.  If not, see <https://www.gnu.org/licenses/>.        

FROM python:3.11.5

WORKDIR /app

COPY requirements.txt .
RUN PIP_DISABLE_PIP_VERSION_CHECK=1 \
    pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y apache2-utils && \
    rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
