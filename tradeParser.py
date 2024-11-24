import requests

class TradeAnalyzer:
    def __init__(self, value_lists):
        self.value_lists = value_lists
        self.price_data = self._fetch_price_data()
        self.valuelist_cache = []

    def _fetch_price_data(self):
        """Fetch price data from the provided URLs."""
        price_data = {}
        for value_list in self.value_lists:
            value_list_name = value_list["info"]["Name"]
            url = value_list["url"]
            columns = value_list["info"]
            response = requests.get(url)
            if response.status_code == 200:
                sheet_data = response.json()
                price_data[value_list_name] = {}
                for entry in sheet_data:
                    item_name = entry[columns["ItemNameColumn"]].strip().lower()
                    try: 
                        price = float(entry[columns["ValueColumn"]].replace(".","").replace(",",""))
                    except ValueError:
                        continue
                    price_data[value_list_name][item_name] = price
        self.price_data = price_data
        return price_data

    def parse_trade_offer(self, trade_offer):
        """Parse the trade offer string into structured data."""
        my_items = []
        your_items = []
        trade_parts = trade_offer.split("my:")[1].split("your:")
        my_section = trade_parts[0].strip()
        your_section = trade_parts[1].strip() if len(trade_parts) > 1 else ""

        my_items = self._parse_items(my_section)
        your_items = self._parse_items(your_section)

        return {"my": my_items, "your": your_items}

    def _fetch_price_data(self):
        """Fetch price data from the provided URLs."""
        price_data = {}
        for value_list in self.value_lists:
            value_list_name = value_list["info"]["Name"]
            url = value_list["url"]
            columns = value_list["info"]
            response = requests.get(url)
            if response.status_code == 200:
                sheet_data = response.json()
                price_data[value_list_name] = {}
                for entry in sheet_data:
                    item_name = entry[columns["ItemNameColumn"]].strip().lower()
                    try: 
                        price = float(entry[columns["ValueColumn"]].replace(".","").replace(",",""))
                        print(price)
                    except ValueError:
                        continue
                    price_data[value_list_name][item_name] = price
        return price_data

    def _parse_items(self, section):
        """Parse items from a trade section."""
        items = []
        item_entries = section.split("]")
        for entry in item_entries:
            if "[" in entry:
                item_data = entry.split("[")[1]
                if "x" in item_data:
                    name, quantity = item_data.rsplit("x", 1)
                    quantity = int(quantity)
                else:
                    name, quantity = item_data, 1
                name = name.strip().lower()
                item_values = {}
                for value_list_name, value_list in self.price_data.items():
                    item_values[value_list_name] = value_list.get(name, 0)
                items.append({"name": name, "quantity": quantity, "values": item_values})
                print(f"Parsing item: {name} with quantity {quantity} and values {item_values}")
        return items

    def analyze_trade(self, trade_offer):
        """Analyze the trade offer and calculate total values."""
        parsed_trade = self.parse_trade_offer(trade_offer)
        my_totals = {}
        your_totals = {}
        for value_list_name in self.price_data.keys():
            my_totals[value_list_name] = sum(item["quantity"] * item["values"][value_list_name] for item in parsed_trade["my"])
            your_totals[value_list_name] = sum(item["quantity"] * item["values"][value_list_name] for item in parsed_trade["your"])
        trade_differences = {value_list_name: abs(my_totals[value_list_name] - your_totals[value_list_name]) for value_list_name in self.price_data.keys()}
        return {"my_totals": my_totals, "your_totals": your_totals, "trade_differences": trade_differences}

value_lists = [
    {"url": "https://opensheet.elk.sh/1tzHjKpu2gYlHoCePjp6bFbKBGvZpwDjiRzT9ZUfNwbY/Alphabetical", "info": {"ValueColumn": "Price", "ItemNameColumn": "Skin Name", "Name":"BVL"}},
    {"url": "https://opensheet.elk.sh/1VqX9kwJx0WlHWKCJNGyIQe33APdUSXz0hEFk6x2-3bU/Sorted+View", "info": {"ValueColumn": "Base Value", "ItemNameColumn": "Name", "Name": "Yzz"}},
    {"url": "https://opensheet.elk.sh/1a6ZUrMt89EgMgl_HzM7zHG6vaQIs5W9_e4tlIadjBrM/1", "info": {"ValueColumn": "Static Value", "ItemNameColumn": "Item", "Name": "RVR"}}
]
if __name__ ==  "__main__":
    analyzer = TradeAnalyzer(value_lists)
    def xd():
        trade_offer = "my:[nova][cargo]x4 your:[cookie][bat]x4"
        result = analyzer.analyze_trade(trade_offer)
        print("My totals:")
        for value_list_name, total in result["my_totals"].items():
            print(f"{value_list_name}: {total}")
        print("Your totals:")
        for value_list_name, total in result["your_totals"].items():
            print(f"{value_list_name}: {total}")
        print("Trade differences:")
        for value_list_name, difference in result["trade_differences"].items():
            print(f"{value_list_name}: {difference}")
    xd()
    xd()
    