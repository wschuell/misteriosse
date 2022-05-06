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
	# current_start_time -= time_delta_big
	# current_end_time -= time_delta_big
	current_start_time -= time_delta_small
	current_end_time -= time_delta_small
	print_time()

### Plot
# Average Impact on single download per dev failing

X = [st for st,res in results]
Y = [res.sum() for st,res in results]

with open(os.path.join(csv_folder,'globalhealth_timeseries.csv'),'w') as f:
	f.write('\n'.join(['{},{}'.format(st.strftime("%Y-%m-%d"),res.sum()) for st,res in results]))

plt.plot(X,Y)
filename = os.path.join(fig_folder,'globalmeasure_timeevol.png')
plt.savefig(filename)

print_time()

