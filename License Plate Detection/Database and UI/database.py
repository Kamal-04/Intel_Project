import sqlite3 as sql
import datetime
class ParkingArea:

    def __init__(self,parking_area_name : str,total_capacity : int, currently_filled = 0 ) -> None:

        # Parameter initialization
        self.name = parking_area_name
        self.total_capacity = total_capacity
        self.currently_filled = currently_filled
        self.avg_occupancy = 0
        self.avg_new_visiting = 0
        self.dates = set()
        self.daily_slot_average = {}
        self.daily_slot_count = {}
        self.slot_unavailable_count = {}
        self.daily_new_visiting = {}
        self.date_format = "%Y-%m-%d"
        self.current_date = datetime.datetime.now()
        

        
        # Database Connetion Initialization
        self._db_name = parking_area_name +  ".db"
        self.parked_table_name = parking_area_name+ "_parked"
        self.record_table_name = parking_area_name+ "_record"
        self.customer_table_name = parking_area_name+ "_customer"

        # Database Creation
        self._db = sql.connect(self._db_name)
        
        # Database Cursor Declaration
        self.db_cur = self._db.cursor()
        self.db_cur.execute(f"CREATE TABLE IF NOT EXISTS {self.parked_table_name} (Car_Number VARCHAR , Date VARCHAR, In_Time VARCHAR)")
        self.db_cur.execute(f"CREATE TABLE IF NOT EXISTS {self.record_table_name} (Car_Number VARCHAR , Date VARCHAR, In_Time VARCHAR , Out_Time VARCHAR)")
        self.db_cur.execute(f"CREATE TABLE IF NOT EXISTS {self.customer_table_name} (Car_Id INTEGER, Car_Number VARCHAR)")
    
    def customer_data_entry(self, vehicle_id : int, vehicle_number : str) -> bool:

        #Adding Customer's Id and Car Number
        try:
            cmd = f'''INSERT INTO {self.customer_table_name} VALUES ( "{vehicle_id}", "{vehicle_number}")'''
            self.db_cur.execute(cmd)
            return True

        except:
            print("Entry failed")
            return False
        

    def entry(self, vechile_id : str, date : str, In_Time : str) -> bool:
        '''
            Adds the car to Parked Table
        '''
        flag = 0
        try:
            # Initialize date in dictionary
            if date not in self.slot_unavailable_count:
                self.slot_unavailable_count[date] = 0
            if date not in self.daily_new_visiting:
                self.daily_new_visiting[date] = 0

            #Check if existing customer or new-comer 
            check_cmd = f"SELECT * FROM {self.customer_table_name} WHERE Car_Number = '{vechile_id}'"
            res = self.db_cur.execute(check_cmd)
            count = res.fetchone()
            if not count:
                self.daily_new_visiting[date] += 1


            

            if self.currently_filled < self.total_capacity:
                cmd = f'''INSERT INTO {self.parked_table_name} VALUES ("{vechile_id}","{date}","{In_Time}")'''
                self.db_cur.execute(cmd)
                self.currently_filled+=1
                
                if date not in self.daily_slot_count:
                    self.daily_slot_count[date] = 1
                else:
                    self.daily_slot_count[date] += 1

                curr_date = datetime.datetime.strptime(date,self.date_format)
                if self.current_date == datetime.datetime.now():
                    self.current_date = curr_date
                else:
                    # if self.current_date != curr_date:
                    #     self.daily_average(date)
                    self.current_date = curr_date
                self.daily_average(date)

                self.dates.add(date)
            else:
                self.slot_unavailable_count[date] += 1
                print("No free parking slots available")
                return False
            return True
        
        except:
            print("Entry Failed")
            return False
    
    
    def exit(self, vechile_id : str , Out_Time : str) -> bool:
        '''
            Remove the car from the Parked Database and Its to the Entry Records 
        '''
        try:
            select_cmd = f"SELECT * FROM {self.parked_table_name} WHERE Car_Number = '{vechile_id}'"
            car_data_cur   = self.db_cur.execute(select_cmd)
            vechile_id,date,In_Time = car_data_cur.fetchone()
            
            push_data = f'''INSERT INTO {self.record_table_name} VALUES ("{vechile_id}","{date}","{In_Time}","{Out_Time}")'''
            self.db_cur.execute(push_data)

            cmd = f"DELETE FROM {self.parked_table_name} WHERE Car_Number = '{vechile_id}'"
            self.db_cur.execute(cmd)
            self.currently_filled-=1

            return True
        except:
            print("Exit Failed")
            return False
        
    def daily_average(self,cur_date : str):
        if cur_date not in self.daily_slot_average:
            self.daily_slot_average[cur_date] = 0
        ct = 0
        try:
            ct = self.daily_slot_count[cur_date]
        except:
            pass
        avg = (ct/self.total_capacity)*100
        self.daily_slot_average[cur_date] = avg
        self.avg_occupancy = sum(self.daily_slot_average.values())/len(self.daily_slot_average)

