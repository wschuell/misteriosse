import socket
import os
import copy
import sys
import json
import csv

import time
from dateutil.relativedelta import relativedelta
import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


import repodepo as rd
from repodepo.getters import SR_getters,rank_getters,policy_getters,effect_rank_getters

show_bool = False

db_conninfo = dict(
					db_host='localhost',
					port=5432,
					db_user='postgres',
					db_type='postgres',
					db_name='rust_repos',
					)

db = rd.repo_database.Database(**db_conninfo)

start_time_str = '2021-01-01'
end_time_str = '2022-01-01'
start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d')
end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d')
iter_max = 50

nb_devs_list = list(range(21))+[25,30,35,40,50,60,75,100]+[150,200,250,300,350,400,500,600,750,1000]+[1500,2000,2500,3000,3500,4000,5000,6000,7500,10000,15000,20000,25000,30000,40000,45000]
max_devs = max(nb_devs_list)

SR_class =  SR_getters.SRGetter # alternatives: SR_getters.SRLinear, SR_getters.SRLeontief, SR_getters.OldSRCobbDouglas
dev_exp = 0.5
deps_exp = 0.5

SR_args = {'dev_cd_power':dev_exp,'deps_cd_power':deps_exp,'iter_max':iter_max,'start_time':start_time,'end_time':end_time,'dl_weights':True,'norm_dl':True}

SR_name = SR_class.__name__.split('.')[-1]
if SR_class == SR_getters.SRGetter:
	SR_name += '__dev{}__deps{}'.format(dev_exp,deps_exp).replace('.','_')

Policy_class = policy_getters.CommitRatePolicyGetter

fig_folder = os.path.join(os.path.dirname(__file__),'generated_figs',db.db_name,SR_name)
csv_folder = os.path.join(os.path.dirname(__file__),'generated_CSVs',db.db_name,SR_name)

for folder in [fig_folder,csv_folder]:
	if not os.path.exists(folder):
		os.makedirs(folder)


time_delta_big = relativedelta(years=1)
time_delta_small = relativedelta(months=1)
min_date = datetime.datetime(2015,1,1)

start = time.time()

def print_time():
	print(datetime.datetime.now(),time.time()-start)


class ComputeRank(object):
	def __init__(self,folderpath,filename=None,ref_db=None):
		if filename is None:
			filename = self.__class__.__name__.split('.')[-1]+'.csv'
		self.filepath = os.path.join(folderpath,filename)
		if ref_db is None:
			self.db = db
		else:
			self.db = ref_db

	def compute(self,save=True):
		self.get()
		if save:
			self.save()

	def get(self):
		raise NotImplementedError

	def check_existence(self):
		return os.path.exists(self.filepath)

	def save(self):
		dirpath = os.path.dirname(self.filepath)
		if not os.path.exists(dirpath):
			os.makedirs(dirpath)
		ser_data = self.serialize(self.ranking_data)
		with open(self.filepath,'w') as f:
			f.write(ser_data)

	def get_reponames(self,ranks=False):
		self.db.cursor.execute('''
			SELECT r.id,s.name,r.owner,r.name,rank() over (order by r.id)
			FROM repositories r
			INNER JOIN sources s
			ON r.source=s.id
			;''')
		if ranks:
			return {int(float(r))-1:'/'.join([s,o,n]) for i,s,o,n,r in db.cursor.fetchall()}
		else:
			return {int(float(i)):'/'.join([s,o,n]) for i,s,o,n,r in db.cursor.fetchall()}

	def serialize(self,r_data):
		reponames = self.get_reponames()
		ans = 'rank,id,value,reponame'
		for i,r in enumerate(zip(r_data[0],r_data[2])):
			ans += '\n'
			ans += ','.join([str(i),str(int(r[0])),str(r[1]),reponames[int(r[0])]])
		return ans

	def load(self,save=True):
		if not self.check_existence():
			self.compute(save=save)
		else:
			ans_indirect = dict()
			with open(self.filepath,'r') as f:
				reader = csv.reader(f)
				a = next(reader)
				for elt in reader:
					if len(a) == 4:
						r,i,v,rn = elt
					else:
						r,i,v = elt
					ans_indirect[int(float(i))] = int(r)

			ans_direct = np.zeros((len(ans_indirect)))
			ans_values = np.zeros((len(ans_indirect)))


			with open(self.filepath,'r') as f:
				reader = csv.reader(f)
				next(reader)
				for elt in reader:
					if len(a) == 4:
						r,i,v,rn = elt
					else:
						r,i,v = elt
					ans_direct[int(r)] = int(float(i))
					# ans_values[int(r)] = float(v)
					ans_values[int(r)] = (np.nan if v=='None' else float(v))

			self.ranking_data = (ans_direct,ans_indirect,ans_values)

class IDRank(ComputeRank):
	def get(self):
		self.ranking_data = rank_getters.RepoRankGetter(db=self.db).get_result()

class StarRank(ComputeRank):
	def get(self):
		self.ranking_data = rank_getters.RepoStarRank(db=self.db,end_time=end_time).get_result()

class DLRank(ComputeRank):
	def get(self):
		self.ranking_data = rank_getters.RepoDLRank(db=db,end_time=end_time,start_time=start_time).get_result()

class DepCountRank(ComputeRank):
	def get(self):
		self.ranking_data = rank_getters.RepoDepRank(db=db,ref_time=end_time).get_result()

class PackageAgeRank(ComputeRank):
	def get(self):
		self.ranking_data = rank_getters.PackageAgeRank(db=db).get_result()

class TransDepCountRank(ComputeRank):
	def get(self):
		self.ranking_data = rank_getters.RepoTransitiveDepRank(db=db,ref_time=end_time).get_result()

class RandomRank(ComputeRank):
	def get(self):
		self.ranking_data = rank_getters.RepoRandomRank(db=db,seed=1).get_result()

class VaccRank(ComputeRank):
	def get(self):
		# vaccgetter = effect_rank_getters.ParallelVaccRankGetter(db=db,start_time=start_time,end_time=end_time,sr_getter_class=SR_class,srgetter_kwargs=SR_args,limit_repos=None,computation_results_db=os.path.join(csv_folder,'vaccrank_cr.db'))
		vaccgetter = effect_rank_getters.ParallelVaccRankGetter(db=db,start_time=start_time,end_time=end_time,sr_getter_class=SR_class,srgetter_kwargs=SR_args,limit_repos=None,computation_results_db=os.path.join(csv_folder,'vaccrank_cr.db'))

		# vaccgetter = effect_rank_getters.VaccinationRankGetter(db=db,start_time=start_time,end_time=end_time,sr_getter_class=SR_class,srgetter_kwargs=SR_args,limit_repos=10,computation_results_db=os.path.join(csv_folder,'vaccrank_cr.db'))
		self.ranking_data = vaccgetter.get_result()


def get_all_rankings(csv_folder,rankings_list):
	ans = []
	for r_name,r_class in rankings_list:
		rk = r_class(folderpath=csv_folder)
		rk.load()
		ans.append((r_name,rk.ranking_data))
	return ans


rankings_list = [
				('Vacc rank',VaccRank),
				# ('ID rank',IDRank),
				('random rank',RandomRank),
				('dep count rank',DepCountRank),
				('trans dep count rank',TransDepCountRank),
				('star rank',StarRank),
				('dl rank',DLRank),
				('age rank',PackageAgeRank),
				]

print_time()
