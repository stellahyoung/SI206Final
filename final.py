import sqlite3
import re
import os
import unittest
import json
import requests
import numpy as np
import scipy.stats
import statistics
import math
import matplotlib.pyplot as plt 
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="d0ce8860de294bb1a60df0cc6504e3e4",
                                               client_secret="eb47802f8ca94578a17d61acdc7f820a",
                                               redirect_uri="http://localhost:1234",
                                               scope="user-library-read"))

# Team Name: Elizabeth + Stella
# Group Members: Stella Young, ELizabeth Kim


# Create database
def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn
#Sets up the database with an input(name of choice). Returns the cursor and the connection to the database

# Get concert data in json
def concert_web():
    web_data = {}
    
    url = "https://www.songkick.com/leaderboards/popular_artists"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    result = soup.find('table')
    row = result.find_all('tr')
    
    for i in range(1, len(row)):
        content = row[i].find('td', class_ = 'concert-count')
        for data in content:
            artist = row[i].select("td")[2].text
            new_data = data.strip()
            numbers = new_data.split(' ')
            web_data[artist.strip()] = str(numbers[0])           

    return web_data
#No inputs. Requests and scrapes songkick website using beautiful soup. 
# Returns a dictionary that has the artist name and the number of their upcoming concerts

# Create Concerts table
def create_concert_table(cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS Concert (Artist TEXT PRIMARY KEY, Concerts INT)")
    conn.commit()

#Takes the dictionary that we got from concert_web, the cursor, and the connection of the database as inputs. Creates the "Concerts" table. Returns nothing. 

def add_into_concert_table(cur,conn, add): 
    dic = concert_web()
    data_key = list(dic.keys())
    starting = 0 + add
    limit = 25 + add
    
    for i in data_key[starting:limit]:
        cur.execute("INSERT OR IGNORE INTO Concert (Artist, Concerts) VALUES (?,?)",(i, dic[i]))
        
    conn.commit()

#Inserts artists' name and number of upcoming concerts into the table. Returns nothing. 


def spotify_api():
    spotify_lst = []
    for name in concert_web().keys():
        results = sp.search(q ='artist:' + name, type = 'artist' )
        #print(results)
        items = results['artists']['items']
        #print(items)
        if len(items)>0:
            artist = items[0]
            if artist not in spotify_lst:
                name = artist['name']
                id = str(artist['id'])
                popularity = str(artist['popularity'])
                tup = (name, id, popularity)
                spotify_lst.append(tup)
    #print(spotify_lst)
    return spotify_lst
            



#creating spotify table
def create_spotify_table(cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS Spotify (id TEXT UNIQUE, popularity NUMBER)")
    conn.commit()


#adding spotify data into database
def add_into_spotify_table(cur, conn, add):
    data = spotify_api()
    data_lst = []
    starting = 0 + add
    limit = 25 + add
    for item in data[starting:limit]:
        id = item[1]
        popularity = str(item[-1])
        data_lst.append((id, popularity))
        for tup in data_lst:
            cur.execute('INSERT OR IGNORE INTO Spotify (id, popularity) VALUES (?,?)', (tup[0], tup[1]))
         
    conn.commit()


#creating follower table
def create_artist_id_table(cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS Spotify_Artist_Id (name TEXT UNIQUE, id TEXT) ")
    conn.commit()

#adding follower data into database
def insert_id_data_table(cur, conn, add):
    data = spotify_api()
    lst = []
    starting = 0 + add
    limit = 25 + add
    for item in data[starting:limit]:
        name = item[0]
        id = item[1]
        lst.append((name, id))
        for tup in lst:
            cur.execute('INSERT OR IGNORE INTO Spotify_Artist_Id (name, id) VALUES (?,?)', (tup[0], tup[1]))
        conn.commit()


#join tables
def join_tables(cur,conn):
    cur.execute("SELECT Concert.Concerts, Spotify.popularity FROM Spotify JOIN Concert ON Spotify.name = Concert.Artist")
    results = cur.fetchall()
    conn.commit()
    
    return results





# Calculate correlation coefficient
def correlation_calc(list_of_tuple):

    concerts_list = []
    popularity_list = []
    concerts_calc = []
    popularity_calc = []
    upper_function = []
    concerts_calc2 = []
    popularity_calc2 = []

   

    #concerts and popularity prices in a list
    for concert_num, popularity_num in list_of_tuple:
        concerts_list.append(concert_num)
        popularity_list.append(popularity_num)
    

    #concerts and popularity prices mean
    concert_avg = statistics.mean(concerts_list)
    popularity_avg = statistics.mean(popularity_list)
    

    #concerts and popularity upper function
    for i in range(len(concerts_list)):
        concerts_calc.append(concerts_list[i] - concert_avg)
        popularity_calc.append(popularity_list[i] - popularity_avg)
    

    for num1, num2 in zip(concerts_calc, popularity_calc):
	    upper_function.append(num1 * num2)
        
    
    upper_final = sum(upper_function)

    #concerts and popularity lower function
    for i in range(len(concerts_list)):
        concerts_calc2.append((concerts_list[i] - concert_avg)**2)
        popularity_calc2.append((popularity_list[i] - popularity_avg)**2)

    lower_function = sum(concerts_calc2) 
    lower_function2 = sum(popularity_calc2)

    lower_function3 = lower_function*lower_function2

    lower_final = math.sqrt(lower_function3)

    final = upper_final/lower_final
    return final

    # Write the correlation coefficient in a file
def write_correlation_calc(filename, correlation):
    with open(filename, "w", newline="") as fileout:
        fileout.write("Correlation between number of concerts and popularity:\n")
        fileout.write(f"The correlation coefficient between number of concerts and popularity was r = {correlation}.\n")
        fileout.close()
        


def create_regression_line(list_of_tuple):
    artist_lst = []
    concert_lst = []

    for artist, concerts in list_of_tuple:
        artist_lst.append(artist)
        concert_lst.append(concerts)

    x = np.array(artist_lst)
    y = np.array(concert_lst)

    slope, intercept, r, p, stderr = scipy.stats.linregress(artist_lst, concert_lst)
    line = f'Regression line: y={intercept:.2f}+{slope:.2f}x, r={r:.2f}'

    fig, ax = plt.subplots()
    plt.title('Artist Popularity vs # of Upcoming Concerts in 2023')
    ax.plot(x, y, linewidth=0, marker='s', label='Data points')
    ax.plot(x, intercept + slope * x, label=line)
    ax.set_xlabel('Artist Popularity')
    ax.set_ylabel('Number of Concerts')
    ax.legend(facecolor='white')
    plt.show()


def create_heatmap(list_of_tuples):
    concerts_list = []
    popularity_list = []

    for concert_num, popularity_num in list_of_tuples:
        concerts_list.append(concert_num)
        popularity_list.append(popularity_num)


    xy = np.array([concerts_list, popularity_list])
    corr_matrix = np.corrcoef(xy).round(decimals=2)

    fig, ax = plt.subplots()
    im = ax.imshow(corr_matrix)
    im.set_clim(-1, 1)
    ax.grid(False)
    ax.xaxis.set(ticks=(0, 1), ticklabels=('Concert #', 'Popularity #'))
    ax.yaxis.set(ticks=(0, 1), ticklabels=('Concert #', 'Popularity #'))
    ax.set_ylim(1.5, -0.5)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, corr_matrix[i, j], ha='center', va='center', color='r')
    cbar = ax.figure.colorbar(im, ax=ax, format='% .2f')
    plt.show()

    #names_lst = []
    #concert_lst = []
    #pop_lst = []
    #for item in list_of_tuples:
     #   concerts = item[0]
     #   popularity = item[1]
        #name = item[2]
      #  concert_lst.append(concerts)
       # pop_lst.append(popularity)


    #data = spotify_api()
    #pop_lst = []
    #pop_name = []
    #for item in data:
        #popularity = item[-1]
        #name = item[0]
        #pop_lst.append(popularity)
        #pop_name.append(name)

    #for i in range(0, len(pop_lst)):
        #pop_lst[i] = int(pop_lst[i])
    
    #pop_new = sorted(pop_lst)

    #dic = concert_web()
    #data_key = list(dic.values())
    #concert_lst = []
    
    #for value in data_key:
        #concert_lst.append(value)

   #X_axis = np.arange(len(pop_lst))

    #plt.bar(X_axis, pop_lst, 0.4, label = 'Artist Popularity')
    #plt.bar(X_axis, concert_lst, 0.4, label = 'Number of Concerts')

   # plt.xlabel('Artists')
    #plt.ylabel('Number')
    #plt.legend()
   # plt.show()


 # unpack a list of pairs into two tuples
    




def main():
    cur, conn = setUpDatabase("final.db")
    create_concert_table(cur, conn)
    cur.execute('SELECT COUNT(*) FROM Concert')
    conn.commit()
    info = cur.fetchall()
    length = info[0][0]

    if length < 25:
        add_into_concert_table(cur, conn, 0)
    elif 25 <= length < 50:
        add_into_concert_table(cur, conn, 25)
    elif 50 <= length < 75:
        add_into_concert_table(cur, conn, 50)
    elif 75 <= length < 100:
        add_into_concert_table(cur, conn, 75)
    elif 100 <= length < 125:
        add_into_concert_table(cur, conn, 100)
    elif 125 <= length < 150:
        add_into_concert_table(cur, conn, 125)
    

    create_spotify_table(cur, conn)
    cur.execute('SELECT COUNT(*) FROM Spotify')
    conn.commit()
    info = cur.fetchall()
    length = info[0][0]

    if length < 25:
        add_into_spotify_table(cur, conn, 0)
    elif 25 <= length < 50:
        add_into_spotify_table(cur, conn, 25)
    elif 50 <= length < 75:
        add_into_spotify_table(cur, conn, 50)
    elif 75 <= length < 100:
        add_into_spotify_table(cur, conn, 75)
    elif 100 <= length < 125:
        add_into_spotify_table(cur, conn, 100)
    elif 125 <= length < 150:
        add_into_spotify_table(cur, conn, 125)



    create_artist_id_table(cur, conn)
    cur.execute('SELECT COUNT(*) FROM Spotify_Artist_Id')
    conn.commit()
    info = cur.fetchall()
    length = info[0][0]

    if length < 25:
        insert_id_data_table(cur, conn, 0)
    elif 25 <= length < 50:
        insert_id_data_table(cur, conn, 25)
    elif 50 <= length < 75:
        insert_id_data_table(cur, conn, 50)
    elif 75 <= length < 100:
        insert_id_data_table(cur, conn, 75)
    elif 100 <= length < 125:
        insert_id_data_table(cur, conn, 100)
    elif 125 <= length < 150:
        insert_id_data_table(cur, conn, 125)




    joint_calc_tup = join_tables(cur, conn)
    print(joint_calc_tup)
    calculations = correlation_calc(joint_calc_tup)
    write_correlation_calc("calculations.txt", calculations)
    create_regression_line(joint_calc_tup)
    create_heatmap(joint_calc_tup)




    

main()



























