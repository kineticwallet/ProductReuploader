import requests
from io import BytesIO
import time

class Main():
    def init(self):
        globals()['fromUniverse'] = int(input("Source Universe: "))
        globals()['toUniverse'] = int(input("Destination Universe: "))

        cookie = open("cookie.txt", "r")
        globals()['cookie'] = ".ROBLOSECURITY=" + cookie.read()
        cookie.close()

        globals()['csrf'] = ""

        globals()['Products'] = str(input("Reupload Products (y/n): "))
        globals()['Passes'] = str(input("Reupload Passes (y/n): "))
        globals()['EmptyToken'] = str(input("Empty ROBLOSECURITY token file on completion? (y/n): "))

        if not self.checkEditAccess(globals()['toUniverse']):
            print(f"You do not have edit access to universe with ID: {globals()['toUniverse']}")
            return
        
        if globals()['Products'] == "Y" or "y":
            allDevProducts = self.getAllDevProducts(globals()['fromUniverse'])

            if allDevProducts != None:
                for product in allDevProducts:
                    product_name = str(product["name"])
                    product_desc = str(product["Description"])
                    product_price = int(product["priceInRobux"])
                    product_image_link = self.getImageLink(product["iconImageAssetId"])

                    Main().uploadDevProduct(product_name, product_desc, product_price, product_image_link)
                    time.sleep(0.1)

        if globals()['Passes'] == "Y" or "y":
            allPasses = self.getAllPasses(globals()['fromUniverse'])

            if allPasses != None:
                for Pass in allPasses["data"]:
                    pass_info = self.getPassInfo(Pass["id"])

                    if pass_info['IsForSale'] == True:
                        pass_name = str(pass_info["Name"])
                        pass_desc = str(pass_info["Description"])
                        pass_price = int(pass_info["PriceInRobux"])
                        pass_image_link = self.getImageLink(pass_info["IconImageAssetId"])

                        Main().uploadGamepass(pass_name, pass_desc, pass_price, pass_image_link)
                        time.sleep(0.1)
        if globals()['EmptyToken'] == "Y" or "y":
            open("cookie.txt", "w").close()

    def getNewHeaders(self):
        headers = {
            'Cookie': globals()['cookie'],
            'x-csrf-token':  globals()['csrf'],
        }

        return headers

    def checkEditAccess(self, targetUniverse):
        authUniverseResponse = requests.get(f'https://develop.roblox.com/v1/universes/{targetUniverse}/configuration', headers = Main().getNewHeaders())

        if authUniverseResponse.status_code != 200:
            responseHeaders = authUniverseResponse.headers

            if responseHeaders.get("x-csrf-token"):
                self.refreshCSRF(responseHeaders)
                self.checkEditAccess()

            if authUniverseResponse.status_code == 403:
                print(authUniverseResponse.text)
                return False
        else:
            return True
        
    def getAllDevProducts(self, targetUniverse):
        allDevProductsResponse = requests.get(f'https://apis.roblox.com/developer-products/v1/universes/{targetUniverse}/developerproducts?pageNumber=1&pageSize=100000', headers = Main().getNewHeaders())

        if allDevProductsResponse.status_code != 200:
            responseHeaders = allDevProductsResponse.headers

            if responseHeaders.get("x-csrf-token"):
                print(allDevProductsResponse.text)
                self.refreshCSRF(responseHeaders)
                self.getAllDevProducts()
            else:
                print(allDevProductsResponse.text)
                return None
        else:
            return allDevProductsResponse.json()

    def getAllPasses(self, targetUniverse):
        allPassesResponse = requests.get(f'https://games.roblox.com/v1/games/{targetUniverse}/game-passes?limit=100&sortOrder=1', headers = Main().getNewHeaders())

        if allPassesResponse.status_code != 200:
            responseHeaders = allPassesResponse.headers

            if responseHeaders.get("x-csrf-token"):
                self.refreshCSRF(responseHeaders)
                self.getAllPasses()
            else:
                print(allPassesResponse.text)
                return None
        else:
            return allPassesResponse.json()

    def getPassInfo(self, passId):
        passInfoRequest = requests.get(f'https://apis.roblox.com/game-passes/v1/game-passes/{passId}/product-info', headers = Main().getNewHeaders())

        if passInfoRequest.status_code == 200:
            return passInfoRequest.json()

    def refreshCSRF(self, responseHeaders):
        try:
            globals()['csrf'] = responseHeaders["x-csrf-token"]
        except Exception as e:
            print("Error fetching a new X-CSRF token:", e)
        else:
            print('Successfully fetched a new X-CSRF token')

    def getImageLink(self, imageAssetId):
        
        if not isinstance(imageAssetId, int):
            return None

        imageResponse = requests.get(f'https://thumbnails.roblox.com/v1/assets?assetIds={imageAssetId}&returnPolicy=PlaceHolder&size=512x512&format=Png&isCircular=false', headers = Main().getNewHeaders())

        if imageResponse.status_code != 200:
            responseHeaders = imageResponse.headers

            if responseHeaders.get("x-csrf-token"):
                self.refreshCSRF(responseHeaders)
                self.getImageLink(imageAssetId)
            else:
                return ""
        else:
            return imageResponse.json()["data"][0]["imageUrl"]

    def uploadDevProduct(self, productName: str, productDescription: str, productPrice: int, productImageLink):
        base_url = f"""https://apis.roblox.com/developer-products/v1/universes/{globals()['toUniverse']}/developerproducts?name={productName}&description={productDescription}&priceInRobux={productPrice}"""

        files = None

        if isinstance(productImageLink, str):
            files = {'imageFile': BytesIO(requests.get(productImageLink).content)}
        

        product_info = {
            'name': productName,
            'description': productDescription,
            'product_price': productPrice,
            'image': ''
        }

        print(f"Creating Product \"{productName}\"")

        response = requests.post(base_url, headers=Main().getNewHeaders())

        if response.status_code != 200:
            print(response.text)
            response_headers = response.headers

            if response_headers.get("x-csrf-token"):
                self.refreshCSRF(response_headers)
                self.uploadDevProduct(productName, productDescription, productPrice, productImageLink)
        else:
            devproduct_id = response.json()["id"]
            product_response = requests.get(f'https://apis.roblox.com/developer-products/v1/developer-products/{devproduct_id}', headers=Main().getNewHeaders())

            if product_response.status_code == 200:
                product_id = product_response.json()["id"]
                print("Product ID: " + str(product_id))

                image_response = requests.post(f'https://apis.roblox.com/developer-products/v1/developer-products/{product_id}/image', headers=Main().getNewHeaders(), files=files)

                if image_response.status_code != 200:
                    print("Failed to upload product image.")

    def uploadGamepass(self, passName: str, passDescription: str, passPrice: int, passImageLink):
        base_url = "https://apis.roblox.com/game-passes/v1/game-passes"

        form_data = {
            "Name": passName,
            "Description": passDescription,
            "UniverseId": globals()['toUniverse'],
        }

        passPrice = str(passPrice)

        files = None

        if passImageLink != None:
            files = {"File": BytesIO(requests.get(passImageLink).content)}

        print(f"Creating Pass \"{passName}\"")
        passResponse = requests.post(base_url, data=form_data, files=files, headers = Main().getNewHeaders())
        #print(passResponse.json())

        if passResponse.status_code != 200:
            print(passResponse.text)
            if passResponse.headers.get("x-csrf-token"):
                self.refreshCSRF(passResponse.headers)
                self.uploadGamepass(passName, passDescription, passPrice, passImageLink)
        else:
            passId = passResponse.json()["gamePassId"]
            print("Pass ID: " + str(passId))

            url = f"https://apis.roblox.com/game-passes/v1/game-passes/{passId}/details"

            data = {
                "IsForSale": "true",
                "Price": passPrice
            }

            passUpdateResponse = requests.post(url, data=data, headers = Main().getNewHeaders())

            if passUpdateResponse.status_code != 200:
                    print("Failed to set pass on sale.")

if __name__ == '__main__':
    Main().init()