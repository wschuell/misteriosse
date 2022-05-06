
# Executing init code from one place only, so that all params keep being the same through all scripts
import os
with open(os.path.join(os.path.dirname(__file__),'init_params_imports.py'),'rb') as f:
	init_code = f.read()
exec(init_code)




rkdata_list = get_all_rankings(csv_folder=csv_folder,rankings_list=rankings_list)

def save_policy(label,nbdev_val_list):
	filename = '{}_{}.csv'.format(Policy_class.__name__.split('.')[-1],label.replace(' ','_'))
	if os.path.exists(os.path.join(csv_folder,filename)):
		with open(os.path.join(csv_folder,filename),'r') as f:
			reader = csv.reader(f)
			next(reader)
			vals = {int(r[0]):float(r[1]) for r in reader}
	else:
		vals = {}
	orig_len = len(vals)
	for n,val in nbdev_val_list:
		vals[int(n)] = val
	vals_list = sorted(vals.items())
	if orig_len<len(vals_list):
		with open(os.path.join(csv_folder,filename),'w') as f:
			f.write('Nb_devs,value')
			for nbd,v in vals_list:
				f.write('\n{},{}'.format(nbd,v))


def plot_addeddevs(label,ranking,baseline=True,show=False,ndevs_list=nb_devs_list,save=True,filename='addeddevs.png'):

	pg = policy_getters.ParallelBatchPolicyGetter(db=db,rank_label=label,nb_devs_list=ndevs_list,policy_getter_args=dict(ranks=ranking,sr_getter_class=SR_class,**SR_args),computation_results_db=os.path.join(csv_folder,'policy_{}_cr.db'.format(label)))

	vals_tuples = sorted([(n,r['globalsum']) for n,r in pg.get_result().items()])

	save_policy(label=label,nbdev_val_list=vals_tuples)

	X = [r[0] for r in vals_tuples]
	Y = [r[1] for r in vals_tuples]

	if baseline:
		plt.plot(X,[Y[0] for _ in Y],label='baseline',linestyle='dashed')
	plt.plot(X,Y,label=label)
	plt.xlabel('Developers added')
	# plt.ylim(bottom=0)
	plt.xscale('log')
	plt.legend()
	if show:
		plt.show()
	if save:
		plt.savefig(os.path.join(fig_folder,label+'_'+filename))

plt.figure()
plot_addeddevs(*rkdata_list[0])


print_time()
###############################""
# for all rankings

baseline = True
plt.figure()
for r in rkdata_list:
	plot_addeddevs(*r,baseline=baseline)
	baseline = False
	print('finished '+r[0])
	print_time()
plt.savefig(os.path.join(fig_folder,'global_addeddevs_{}.png'.format(max_devs)))


print_time()

