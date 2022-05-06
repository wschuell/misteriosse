# Executing init code from one place only, so that all params keep being the same through all scripts
import os
with open(os.path.join(os.path.dirname(__file__),'init_params_imports.py'),'rb') as f:
	init_code = f.read()
exec(init_code)





current_start_time = start_time
current_end_time = end_time

results = []

print_time()
while current_start_time>= min_date:
	print(current_start_time)
	current_SR_args = copy.deepcopy(SR_args)
	current_SR_args['start_time'] = current_start_time
	current_SR_args['end_time'] = current_end_time
	sr_getter = SR_class(db=db,**current_SR_args)
	results = [(current_end_time,sr_getter.get_result())] + results
	current_start_time -= time_delta_big
	current_end_time -= time_delta_big
	print_time()

### Plot
# Average Impact on single download per dev failing

def plot(dtr,axis=0,title='',show=True,label=None):
	# if ax is None:
	# 	ax_new = plt.plot([np.nan]+sorted(dtr.sum(axis=axis).flat,reverse=True))
	# else:
	# 	ax_new = ax.plot([np.nan]+sorted(dtr.sum(axis=axis).flat,reverse=True))
	plt.plot([np.nan]+sorted(dtr.sum(axis=axis).flat,reverse=True),label=label)
	plt.xscale('log')
	plt.yscale('log')
	if axis == 0:
		plt.xlabel('Developer rank')
	else:
		plt.xlabel('Package rank')
	plt.title('{} axis={}'.format(title,axis))
	if show:
		plt.show()

for st,res in results:
	plot(res,axis=0,title='DLs',show=show_bool,label=str(st))
plt.legend()
filename=os.path.join(fig_folder,'devs_plateau_timeevol.png')
plt.savefig(filename)

print_time()


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

def dev_sorted_func(devs_sorted,filepath):
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

for st,res in results:
	devs_sorted = sorted(enumerate(res.sum(axis=0).flat),reverse=True,key=lambda x:x[1])
	dev_sorted_func(devs_sorted=devs_sorted,filepath=os.path.join(csv_folder,'devs_sorted_{}.csv'.format(st.strftime("%Y-%m-%d"))))

print_time()
