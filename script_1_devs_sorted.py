# Executing init code from one place only, so that all params keep being the same through all scripts
import os
with open(os.path.join(os.path.dirname(__file__),'init_params_imports.py'),'rb') as f:
	init_code = f.read()
exec(init_code)






sr_getter = SR_class(db=db,**SR_args)
deps_to_repo = sr_getter.get_result()
devs_sorted = sorted(enumerate(deps_to_repo.sum(axis=0).flat),reverse=True,key=lambda x:x[1])


### Plot
# Average Impact on single download per dev failing

def plot(dtr,axis=0,title='',show=True,filename='average_impact_per_dev.png'):
	# if ax is None:
	# 	ax_new = plt.plot([np.nan]+sorted(dtr.sum(axis=axis).flat,reverse=True))
	# else:
	# 	ax_new = ax.plot([np.nan]+sorted(dtr.sum(axis=axis).flat,reverse=True))
	plt.plot([np.nan]+sorted(dtr.sum(axis=axis).flat,reverse=True))
	plt.xscale('log')
	plt.yscale('log')
	if axis == 0:
		plt.xlabel('Developer rank')
	else:
		plt.xlabel('Package rank')
	plt.title('{} axis={}'.format(title,axis))
	if show:
		plt.show()
	plt.savefig(filename)

plot(deps_to_repo,axis=0,title='DLs',show=show_bool,filename=os.path.join(fig_folder,'devs_plateau.png'))

### CSV
def get_dev_logins(id_type='github_login'):
	if db.db_type == 'postgres':
		db.cursor.execute('''
			SELECT identity,i.user_id,u.rk-1 from identities i
		inner join identity_types it
		on it.id=i.identity_type_id
		and it.name=%(id_type)s
		inner join (select rank() over (order by uu.id) as rk,id from users uu) as u
		on i.user_id =u.id;
			''',{'id_type':id_type})
	else:
		db.cursor.execute('''
			SELECT identity,i.user_id,u.rk-1 from identities i
		inner join identity_types it
		on it.id=i.identity_type_id
		and it.name=:id_type
		inner join (select rank() over (order by uu.id) as rk,id from users uu) as u
		on i.user_id =u.id;
			''',{'id_type':id_type})
	return {rk:(ulogin,uid) for (ulogin,uid,rk) in db.cursor.fetchall()}

dev_logins_github = get_dev_logins(id_type='github_login')
dev_logins_gitlab = get_dev_logins(id_type='gitlab_login')

def dev_sorted_func(filepath):
	with open(filepath,'w') as f:
		for dev,val in devs_sorted:
			try:
				login = dev_logins_github[dev]
			except KeyError:
				try:
					login = ('GITLAB_'+dev_logins_gitlab[dev][0],dev_logins_gitlab[dev][1])
				except KeyError:
					login = 'NOGHGLLOGIN'
			f.write('{},{},{}\n'.format(login,dev,val))

dev_sorted_func(filepath=os.path.join(csv_folder,'devs_sorted.csv'))

print_time()

#######CSV with explanations

reponames_rk = ComputeRank(folderpath=csv_folder).get_reponames(ranks=True)

devs_mat = sr_getter.devs_mat.copy()
devs_mat_full = sr_getter.devs_getter.get_result(abs_value=True)

def dev_explanations_func(filepath,dev_limit=100,repo_limit=10):
	dev_info = []
	total_dl = sr_getter.dl_vec.sum()
	# deps to repo isolate first N

	# find logins
	for dev,val in devs_sorted[:dev_limit]:
		try:
			login = dev_logins_github[dev]
		except KeyError:
			try:
				login = ('GITLAB_'+dev_logins_gitlab[dev][0],dev_logins_gitlab[dev][1])
			except KeyError:
				login = 'NOGHGLLOGIN'
		dev_info.append({'login':login,'val':val,'dev_orig_rk':dev})
	# get orig ranks
	orig_ranks_direct,orig_ranks_indirect,orig_values = rank_getters.UserRankGetter(db=db).get_result()
	# for each dev
	filecontent = 'dev_rank(by total influence),'
	filecontent += 'reporank(for dev),'
	filecontent += 'login(+user id),'
	filecontent += 'dev_orig_rank(rank in id values),'
	filecontent += 'val(total impact),'
	filecontent += 'reponame,'
	filecontent += 'nbcommits_dev(nb of commits of dev in repo),'
	filecontent += 'sharecommits_dev (in repo),'
	filecontent += 'repo_impact(percentage of impact on repo (between 0 and 1)),'
	filecontent += 'abs_impact(total impact in DLs due to repo+dev),'
	filecontent += 'rel_impact(part of total impact due to repo+dev=same as before but divided by total DLs),'
	filecontent += 'total DLs of repo\n'
	for dev_rank in range(len(dev_info)):
		dev_orig_rk = dev_info[dev_rank]['dev_orig_rk']
		dev_vec = deps_to_repo.getcol(dev_orig_rk).tocoo()

		dev_repolist = sorted(list(zip(dev_vec.row, dev_vec.data)),key=lambda x:-x[1])

	# for each package find name/repo
		for repo_dev_rank,repo in enumerate(dev_repolist[:repo_limit]):
	# compute stuff
	# output file
			repo_dls = sr_getter.dl_vec[repo[0]]
			impact_dls = total_dl * repo[1]
			impact_repo = total_dl * repo[1] / repo_dls
			filecontent += '{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(dev_rank,
					repo_dev_rank+1,
					dev_info[dev_rank]['login'],
					dev_info[dev_rank]['dev_orig_rk'],
					dev_info[dev_rank]['val'],
					reponames_rk[repo[0]],# reponame,
					devs_mat_full[repo[0],dev_info[dev_rank]['dev_orig_rk']],# nbcommits_dev,
					devs_mat[repo[0],dev_info[dev_rank]['dev_orig_rk']],# sharecommits_dev,
					# 'PH',# nb_repos_dev,
					impact_repo,# repo_impact,
					impact_dls,# abs_impact,
					repo[1],# rel_impact,
					repo_dls,#total dls of repo
					)
			if reponames_rk[repo[0]] == 'GitHub/rust-random/rand':
				rid = repo[0]

	with open(filepath,'w') as f:
		f.write(filecontent)
	# print(sr_getter.deps_mat.getrow(rid))
	# print(sr_getter.deps_mat.getcol(rid))

dev_explanations_func(filepath=os.path.join(csv_folder,'devs_sorted_explanations.csv'))
print_time()

dev_explanations_func(filepath=os.path.join(csv_folder,'1st_dev_explanations.csv'),dev_limit=1,repo_limit=32000)

print_time()

