from django.shortcuts import render
import pandas as pd
import json
import requests
# Create your views here.


def index(request, funder=''):
    
    data = {
        'token': '',
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'csvDelimiter': '',
        'rawOrLabel': 'label',
        'rawOrLabelHeaders': 'raw',
        'exportCheckboxLabel': 'false',
        'exportSurveyFields': 'false',
        'exportDataAccessGroups': 'false',
        'returnFormat': 'json'
    }
    
    r = requests.post('https://redcap.h3abionet.org/redcap/api/', data=data)
    # print('HTTP Status: ' + str(r.status_code))
    records = r.json()

    collection_data = {}
    for record in records:
        record_id = record['record_id']
        project_name = record['project_name']
        proj_expected = record['total_expected_parti_pants']
        proj_collected = record['how_many_participant_oject']
        funder_name = record['funder_name']
        for special in [' ']:
            funder_name = funder_name.replace(special, '_').lower()
        for special in ['/']:
            funder_name = funder_name.replace(special, '-').lower()
        if funder != '':
            if funder_name == funder.lower():
                if record_id not in collection_data:
                    collection_data[record_id] = { 'project_id': record_id }
                if project_name != '':
                    if project_name not in collection_data[record_id]:
                        collection_data[record_id]['project_name'] = project_name
                if proj_expected != '':
                    if 'expected' not in collection_data[record_id]:
                        collection_data[record_id]['expected'] = []
                    collection_data[record_id]['expected'].append(proj_expected)
        else:
            if record_id not in collection_data:
                collection_data[record_id] = {'project_id': record_id}
            if project_name != '':
                if project_name not in collection_data[record_id]:
                    collection_data[record_id]['project_name'] = project_name
            if proj_expected != '':
                if 'expected' not in collection_data[record_id]:
                    collection_data[record_id]['expected'] = []
                collection_data[record_id]['expected'].append(proj_expected)
        if proj_collected != '' and record_id in collection_data:
            if 'collected' not in collection_data[record_id]:
                collection_data[record_id]['collected'] = []
            collection_data[record_id]['collected'].append(
                proj_collected)


    ### Project data
    project_data = {}
    for record in collection_data:
        if 'project_name' in collection_data[record] and record not in ['project_name']:
            project_data[collection_data[record]['project_name']] = collection_data[record]
            
    ### Number of projects
    project_names = [ ]
    project_names1 = [ ]
    for project_name in project_data:
        prj = project_data[project_name]['project_name']
        project_names1.append(prj)
        prj_id = project_data[project_name]['project_id']
        prj = f'<a href="/dashboard/projects/{prj_id}">{prj}</a>'
        project_names.append(prj)

    ### Get total expected
    projects_expected = []
    for project_name in project_data:
        if 'expected' in project_data[project_name]:
            projects_expected.append(int(project_data[project_name]['expected'][-1]))
        else:
            projects_expected.append(0)
        
    ### Get total collected
    projects_collected = []
    for project_name in project_data:
        if 'collected' in project_data[project_name]:
            projects_collected.append(int(project_data[project_name]['collected'][-1]))
        elif 'collected' not in project_data[project_name] and 'expected' in project_data[project_name]:
            projects_collected.append(0)
        
    ### Progress
    progress = round(sum(projects_collected) * 100 / sum(projects_expected))
    
    ### Table content
    table_data = pd.DataFrame(list(zip(project_names1, projects_expected, projects_collected)), columns=[
                        'Project', 'Expected', 'Recruited'])
    table_content = table_data.to_html(index=None)
    table_content = table_content.replace("", "")
    table_content = table_content.replace(
        'class="dataframe"', "id='big_tables' class='table table-striped table-bordered'")
    table_content = table_content.replace('border="1"', "")

    context = {"overal_expected": f"{sum(projects_expected):,}",
               "overal_collected": f"{sum(projects_collected):,}",
               "projects": project_names,
               "project_data": project_data,
               "no_projects": len(project_names),
               "progress": progress,
               "projects_collected": projects_collected,
               "projects_expected": projects_expected,
               'table_data': table_content,
               'all_records': records}

    return render(request, 'index.html', context=context)


def projectdetail(request, pid):
    """
    For a single project
    """
    data = {
        'token': 'FE963F701FC2107DFD66D4319BA8F8D2',
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'csvDelimiter': '',
        'records[0]': pid,
        'rawOrLabel': 'label',
        'rawOrLabelHeaders': 'raw',
        'exportCheckboxLabel': 'false',
        'exportSurveyFields': 'false',
        'exportDataAccessGroups': 'false',
        'returnFormat': 'json'
    }

    r = requests.post('https://redcap.h3abionet.org/redcap/api/', data=data)
    records = r.json()
    
    ### Get collections
    collections = [ record['redcap_event_name']
                   for record in records if 'Login' != record['redcap_event_name'] ]
    # if len(collections) == 0:
    
    ### Build data object for project
    project_data = {}
    sites = {}
    site_names = []
    variable_names = []
    for record in records:
        project_id = record['record_id']
        if record['redcap_event_name'] == 'Login':
            project_data['project_details'] = record
            ### Get sites
            for rec in record:
                if rec.startswith("site_") and record[rec] != '':
                    sites[rec] = (record[rec])
                    site_names.append(record[rec])
        else:
            project_data[record['redcap_event_name']] = record
            ### Get queestions/variables #TODO need to link these to actual questions
            for rec in record:
                if rec.startswith("q0") and record[rec] != '':
                    rec = rec.split('_')
                    var = f'{rec[0]}_{rec[1]}'
                    if var not in variable_names and 'q02_8' not in var: ### ignoring YES/NO questions
                        variable_names.append(var)
    
    ### Site data
    site_data = {}
    for col in collections:
        if col not in site_data:
            site_data[col] = {}
            for site in site_names:
                site_data[col][site] = []
        for dat in project_data[col]:
            if dat.startswith("q0") and 'q02_8' not in dat:
                if project_data[col][dat] != '':
                    for i in range(len(sites)+1):
                        if dat.endswith(f'_{i}'):
                            # if dat not in variables:
                            #     variables[site_names[i-1]].append(dat)
                            site_data[col][site_names[i-1]].append(project_data[col][dat])

    ### Create data for each question/variable
    variable_data = {}
    for var in variable_names:
        var_idx = variable_names.index(var)
        if var not in variable_data:
            variable_data[var] = []
        for site in site_data[collections[-1]]:
            if len(collections[-1]) != 0 and len(site_data[collections[-1]][site]) != 0:
                variable_data[var].append(int(site_data[collections[-1]][site][var_idx]))
            else:
                variable_data[var].append(0)
    
    ### Creating JSON series
    import json 
    series = []
    for var in variable_data:
        # Data to be written 
        s = {
                'name': var,
                'data': variable_data[var],
                'tooltip': {
                    'valueSuffix': ' Participants'
                },
                'pointPadding': 0.0,
                'pointPlacement': 0.0,
                'yAxis': 0,
            }
        series.append(s)
            
    ### Progress
    overall_expected = project_data['project_details']['total_expected_parti_pants']
    if len(collections) != 0 and project_data[collections[-1]]['how_many_participant_oject'] != '':
        overall_recruited = project_data[collections[-1]]['how_many_participant_oject']
    else:
        overall_recruited = 0
    progress = round(int(overall_recruited) * 100 / int(overall_expected))
    
    ### Collection data
    collection_data = {}
    for col in collections:
        if 'collected' not in collection_data:
            collection_data['collected'] = []
            collection_data['expected'] = []
        if len(collections) != 0 and project_data[col]['how_many_participant_oject'] != '':
            collect = project_data[col]['how_many_participant_oject']
        else:
            collect = 0
        collection_data['collected'].append(int(collect))
        collection_data['expected'].append(int(project_data['project_details']['total_expected_parti_pants']))
    
    context = {
        'project': project_data,
        'overall_expected': overall_expected, 
        'overall_recruited': overall_recruited, 
        'progress': progress, 
        'sites': sites,
        'site_names': site_names,
        'variable_data': variable_data,
        'series': series,
        'collections': collections,
        'collection_data': collection_data,
    }
    
    return render(request, 'project.html', context=context)
