
# Executing init code from one place only, so that all params keep being the same through all scripts
import os
with open(os.path.join(os.path.dirname(__file__),'init_params_imports.py'),'rb') as f:
	init_code = f.read()
exec(init_code)


get_all_rankings(csv_folder=csv_folder,rankings_list=rankings_list)
print_time()

sys.exit(0)

ranks = rank_getters.RepoRankGetter(db=db).get_result()

if not os.path.exists('vaccdirect.csv'):
	vaccgetter = effect_rank_getters.VaccinationRankGetter(db=db,start_time=start_time,end_time=end_time,sr_getter_class=SR_class,srgetter_kwargs=SR_args)
	ranks_vacc = vaccgetter.get_result()

	ans_direct,ans_indirect = ranks_vacc
	with open('vaccdirect.csv','w') as f:
		f.write('\n'.join(['{},{}'.format(i,j) for i,j in enumerate(ans_direct)]))
	with open('vaccindirect.csv','w') as f:
		f.write('\n'.join(['{},{}'.format(i,j) for i,j in ans_indirect.items()]))
	with open('vaccresults.json','w') as f:
		f.write(json.dumps(vaccgetter.results))
else:
	with open('vaccdirect.csv','r') as f:
		reader = csv.reader(f)
		reader = list(reader)
		ans_direct = np.asarray([int(float(j)) for i,j in reader])
	with open('vaccindirect.csv','r') as f:
		reader = csv.reader(f)
		ans_indirect = {int(i):int(j) for i,j in reader}
	vaccgetter = effect_rank_getters.VaccinationRankGetter(db=db,start_time=start_time,end_time=end_time,sr_getter_class=SR_class,srgetter_kwargs=SR_args)
	# with open('vaccindirect.json','r') as f:
	# 	vaccgetter.results = json.loads(f.read())
	ranks_vacc = (ans_direct,ans_indirect)

def plot_vaccrk(vaccgetter,title='Vaccination rank',sortfunc='globalsum',show=True,filename='vaccimpacts.png'):
	plt.figure()
	plt.plot([np.nan]+sorted(vaccgetter.results,key=lambda x:x[sortfunc],reverse=True))
	plt.xscale('log')
	plt.yscale('log')
	plt.xlabel('Package rank')
	plt.title('{} per {}'.format(title,sortfunc))
	if show:
		plt.show()
	else:
		plt.savefig(sortfunc+'_'+filename)

def plot_vaccrk_withref(vacc_getter,title='Vaccination rank',sortfunc='globalsum',show=True,filename='vaccimpacts.png'):
	val = vacc_getter.baseline_results[sortfunc]
	plt.figure()
	plt.plot([np.nan]+[val for xx in vacc_getter.results],linestyle='dashed')
	plt.plot([np.nan]+[val-xx for xx in sorted(vacc_getter.results,key=lambda x:x[sortfunc],reverse=True)])
	plt.xscale('log')
	plt.yscale('log')
	plt.xlabel('Package rank')
	plt.title('{} per {}'.format(title,sortfunc))
	if show:
		plt.show()
	else:
		plt.savefig(sortfunc+'_withref_'+filename)


print_time()
###############################""
# diverse rankings


ranks = []

ranks.append(('Vacc rank',ranks_vacc))


ranks.append(('ID rank',rank_getters.RepoRankGetter(db=db).get_result()))

# DLs
ranks.append(('dl rank',rank_getters.RepoDLRank(db=db).get_result()))

# deps
ranks.append(('dep count rank',rank_getters.RepoDepRank(db=db).get_result()))

# transitive deps
ranks.append(('trans dep count rank',rank_getters.RepoTransitiveDepRank(db=db).get_result()))

# stars
ranks.append(('Star rank',rank_getters.RepoStarRank(db=db).get_result()))

print_time()




def plot_addeddevs(label,ranking,baseline=True,show=False,maxdevs=max_devs,save=True,filename='addeddevs.png'):
	ans = []
	for nb_devs in range(maxdevs+1):
		print(label,'{}/{}'.format(nb_devs,maxdevs))
		# p_res = policy_getters.PolicyGetter(db=db,ranks=ranking,nb_devs=nb_devs,dl_weights=True,sr_getter_class=SR_class,**SR_args).get_result()   # policy of adding devs doing as many commits as the max contributor
		p_res = policy_getters.CommitRatePolicyGetter(db=db,ranks=ranking,nb_devs=nb_devs,daily_commits=5./7.,sr_getter_class=SR_class,**SR_args).get_result()
		ans.append(p_res.sum())

	if baseline:
		plt.plot([ans[0] for _ in ans],label='baseline',linestyle='dashed')
	plt.plot(ans,label=label)
	plt.xlabel('Developers added')
	# plt.ylim(bottom=0)
	plt.legend()
	if show:
		plt.show()
	elif save:
		plt.savefig(label+'_'+filename)



print_time()
###############################""
# for all rankings

baseline = True
plt.figure()
for r in ranks:
	plot_addeddevs(*r,baseline=baseline,save=False)
	baseline = False
plt.savefig('global_addeddevs_{}.png'.format(max_devs))


print_time()
