import requests
from io import BytesIO
import time

def ratlimitedRequest(method, url, headers=None, data=None, files=None):
    try:
        response = requests.request(method, url, headers=headers, data=data, files=files)

        if response.status_code == 403 and 'x-csrf-token' in response.headers:
            globals()['csrf'] = response.headers['x-csrf-token']
            if 

def make_request_with_retry(method, url, headers=None, data=None, files=None, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, headers=headers, data=data, files=files)

            # Handle CSRF token refresh
            if response.status_code == 403 and 'x-csrf-token' in response.headers:
                globals()['csrf'] = response.headers['x-csrf-token']
                if headers is not None:
                    headers['x-csrf-token'] = globals()['csrf']
                print('Refreshed CSRF token, retrying request...')
                continue

            # Rate limited or approaching limit
            remaining = response.headers.get('x-ratelimit-remaining')
            reset = response.headers.get('x-ratelimit-reset')

            if response.status_code == 429 or (remaining is not None and reset is not None and remaining == '0'):
                wait_time = int(reset)
                print(f'Rate limit hit. Waiting {wait_time} seconds before retrying...')
                time.sleep(wait_time)
                continue

            # Server errors (retryable)
            if response.status_code in [500, 502, 503, 504]:
                print(f'Server error ({response.status_code}). Retrying...')
                time.sleep(1)
                continue

            # Success or unhandled error
            return response

        except requests.RequestException as e:
            print(f"Request error: {e}")
            time.sleep(1)

    raise Exception(f"Failed after {max_retries} attempts.")



class Main():
    def init(self):
        globals()['fromUniverseId'] = int(input('Source Universe: '))
        globals()['toUniverseId'] = int(input('Destination Universe: '))

        cookie = open('cookie.txt', 'r')
        globals()['cookie'] = f'.ROBLOSECURITY={cookie.read()}'
        cookie.close()

        globals()['csrf'] = ''

        globals()['reuploadPasses'] = bool(input('Reupload Passes (y/n): ').lower() == 'y')
        globals()['reuploadProducts'] = bool(input('Reupload Products (y/n): ').lower() == 'y')

        if not self.checkEditAccess(globals()['fromUniverseId'], globals()['toUniverseId']):
            print(f'Missing universe access permission for {globals()['fromUniverseId']} or {globals()['toUniverseId']}')
            return
        
        if globals()['reuploadPasses'] == True:
            all_passes = self.getAllPasses(globals()['fromUniverseId'])                   

            if all_passes != None:
                infos = {}
                
                for gamepass in all_passes:   
                    id = int(gamepass['id'])
                    infos[id] = self.getPassInfo(id)

                image_urls = self.getImageURLs(*list(infos.values()))                    

                for gamepass in all_passes:
                    id = int(gamepass['id'])
                    info = infos[id]
                    icon_image_asset_id = info.get('IconImageAssetId')
                    self.uploadPass(str(gamepass['name']), str(info['Description']), gamepass['price'], image_urls.get(icon_image_asset_id, '') if icon_image_asset_id is not None else '', id)
                    
        
        if globals()['reuploadProducts'] == True:
            all_products = self.getAllDevProducts(globals()['fromUniverseId'])
            image_urls = self.getImageURLs(*all_products)
            
            if all_products != None:
                for product in all_products:
                    icon_image_asset_id = product.get('IconImageAssetId')
                    self.uploadProduct(str(product['Name']), str(product['Description']), product['PriceInRobux'], image_urls.get(icon_image_asset_id, '') if icon_image_asset_id is not None else '', int(product['ProductId']), int(product['DeveloperProductId']))       
        '''
        if globals()['reuploadProducts'] == True:
            allDevProducts = self.getAllDevProducts(globals()['fromUniverse'])

            if allDevProducts != None:
                for product in allDevProducts:
                    product_name = str(product['name'])
                    product_desc = str(product['Description'])
                    product_price = int(product['priceInRobux'])
                    product_image_link = self.getImageLink(product['iconImageAssetId'])
                    old_product_id = int(product['id'])

                    Main().uploadDevProduct(product_name, product_desc, product_price, product_image_link, old_product_id)
                    time.sleep(0.1)

        if globals()['reuploadPasses'] == True:
            allPasses = self.getAllPasses(globals()['fromUniverse'])

            if allPasses != None:
                for Pass in allPasses['data']:
                    pass_info = self.getPassInfo(Pass['id'])

                    if pass_info['IsForSale'] == True:
                        pass_name = str(pass_info['Name'])
                        pass_desc = str(pass_info['Description'])
                        pass_price = int(pass_info['PriceInRobux'])
                        pass_image_link = self.getImageLink(pass_info['IconImageAssetId'])
                        old_pass_id = int(pass_info['TargetId'])

                        Main().uploadGamepass(pass_name, pass_desc, pass_price, pass_image_link, old_pass_id)
                        time.sleep(0.1)
                        '''

    def getNewHeaders(self):
        return {
            'Cookie': globals()['cookie'],
            'x-csrf-token':  globals()['csrf'],
        }

   ##def refreshCSRF(self, headers):
   ##    try:
   ##        globals()['csrf'] = str(headers['x-csrf-token'])
   ##    except Exception as e:
   ##        print('Error fetching a new X-CSRF token:', e)
   ##    else:
   ##        print('Successfully fetched a new X-CSRF token')    

    def checkEditAccess(self, *args):
        response = make_request_with_retry("GET", f'https://develop.roblox.com/v1/universes/multiget/permissions?{'&'.join(f'ids={arg}' for arg in args)}', headers = self.getNewHeaders())

        if response.status_code != 200 or response.status_code == 403:
                print(response.text)
                return False
        else:
            for universe in response.json().get('data', []):
                if not universe.get('canManage') or not universe.get('canCloudEdit'):
                    return False

            return True    
        
    def getAllDevProducts(self, fromUniverseId: int):
        response = make_request_with_retry("GET", f'https://apis.roblox.com/developer-products/v2/universes/{fromUniverseId}/developerproducts?limit=100000', headers = self.getNewHeaders())

        if response.status_code != 200:
            print(response.text)
            return None
        else:
            return response.json().get('developerProducts', [])

    def getAllPasses(self, fromUniverseId: int, cursor=None, passes=None):
        response = make_request_with_retry("GET", f'https://games.roblox.com/v1/games/{fromUniverseId}/game-passes?limit=100&sortOrder=1{f'&cursor={cursor}' if isinstance(cursor, str) else ''}', headers = self.getNewHeaders())

        if response.status_code != 200:
            print(response.text)
            return None
        else:
            json_response = response.json()
            next_page_cursor = json_response.get('nextPageCursor')

            if next_page_cursor != None:
                return self.getAllPasses(fromUniverseId, next_page_cursor, json_response.get('data', []))
            else:
                data = json_response.get('data', [])
                data.extend(passes if passes != None else [])
                return data

    def getPassInfo(self, id: int):
        response = make_request_with_retry("GET", f'https://apis.roblox.com/game-passes/v1/game-passes/{id}/product-info', headers = self.getNewHeaders())

        if response.status_code != 200:
            print(response.text)
            return {}
        else:
            return response.json()

    def getImageURLs(self, *args):
        response = make_request_with_retry("GET", f'https://thumbnails.roblox.com/v1/assets?assetIds={','.join(f'{arg.get('IconImageAssetId', 0)}' for arg in args if (id := arg.get('IconImageAssetId')) is not None)}&returnPolicy=PlaceHolder&size=512x512&format=Png&isCircular=false', headers = self.getNewHeaders())

        if response.status_code != 200:
            print(response.text)
            return {}
        else:
            image_urls = {}

            for image in response.json().get('data', []):
                target_id = image.get('targetId')
                image_url = image.get('imageUrl')

                if target_id and image_url:
                    image_urls[target_id] = image_url
                
            return image_urls                   

    def uploadPass(self, name: str, description: str, priceInRobux: int, imageLink: str, passId: int):
        print("PASS:", imageLink)
        ##base_url = 'https://apis.roblox.com/game-passes/v1/game-passes'
##
        ##form_data = {
        ##    'Name': passName,
        ##    'Description': passDescription,
        ##    'UniverseId': globals()['toUniverse'],
        ##}
##
        ##passPrice = str(passPrice)
##
        ##files = None
##
        ##if passImageLink != None:
        ##    files = {'File': BytesIO(requests.get(passImageLink).content)}
##
        ##print(f'Creating Pass \'{passName}\'')
        ##print(f'Old pass ID: {oldPassID}')
        ##passResponse = requests.post(base_url, data=form_data, files=files, headers = Main().getNewHeaders())
##
        ##if passResponse.status_code != 200:
        ##    print(passResponse.text)
        ##    if passResponse.headers.get('x-csrf-token'):
        ##        self.refreshCSRF(passResponse.headers)
        ##        self.uploadGamepass(passName, passDescription, passPrice, passImageLink, oldPassID)
        ##else:
        ##    passId = passResponse.json()['gamePassId']
        ##    print('Pass ID: ' + str(passId))
##
        ##    url = f'https://apis.roblox.com/game-passes/v1/game-passes/{passId}/details'
##
        ##    data = {
        ##        'IsForSale': 'true',
        ##        'Price': passPrice
        ##    }
##
        ##    passUpdateResponse = requests.post(url, data=data, headers = Main().getNewHeaders())
##
        ##    if passUpdateResponse.status_code != 200:
        ##            print('Failed to set pass on sale.')

    def uploadProduct(self, name: str, description: str, priceInRobux: int, imageLink: str, productId: int, developerProductId: int):
        print("PRODUCT:", imageLink)
        ##base_url = f'''https://apis.roblox.com/developer-products/v1/universes/{globals()['toUniverse']}/developerproducts?name={productName}&description={productDescription}&priceInRobux={productPrice}'''
##
        ##files = None
##
        ##if isinstance(productImageLink, str) and productImageLink != '':
        ##    files = {'imageFile': BytesIO(requests.get(productImageLink).content)}
        ##
##
        ##product_info = {
        ##    'name': productName,
        ##    'description': productDescription,
        ##    'product_price': productPrice,
        ##    'image': ''
        ##}
##
        ##print(f'Creating Product \'{productName}\'')
##
        ##devproduct_id = oldProductID
        ##product_response = requests.get(f'https://apis.roblox.com/developer-products/v1/developer-products/{devproduct_id}', headers=Main().getNewHeaders())
##
        ##if product_response.status_code != 200:
        ##    if product_response.get('x-csrf-token'):
        ##        self.refreshCSRF(product_response)
        ##        self.uploadDevProduct(productName, productDescription, productPrice, productImageLink, oldProductID)
        ##else:
        ##    product_id = product_response.json()['id']
        ##    print('Old product ID: ' + str(product_id))
##
        ##response = requests.post(base_url, headers=Main().getNewHeaders())
##
        ##if response.status_code != 200:
        ##    print(response.text)
        ##    response_headers = response.headers
##
        ##    if response_headers.get('x-csrf-token'):
        ##        self.refreshCSRF(response_headers)
        ##        self.uploadDevProduct(productName, productDescription, productPrice, productImageLink, oldProductID)
        ##else:
        ##    devproduct_id = response.json()['id']
        ##    product_response = requests.get(f'https://apis.roblox.com/developer-products/v1/developer-products/{devproduct_id}', headers=Main().getNewHeaders())
##
        ##    if product_response.status_code == 200:
        ##        product_id = product_response.json()['id']
        ##        print('Product ID: ' + str(product_id))
##
        ##        image_response = requests.post(f'https://apis.roblox.com/developer-products/v1/developer-products/{product_id}/image', headers=Main().getNewHeaders(), files=files)
##
        ##        if image_response.status_code != 200:
        ##            print('Failed to upload product image.')      

if __name__ == '__main__':
    Main().init()