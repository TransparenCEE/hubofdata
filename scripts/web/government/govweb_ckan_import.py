#!/usr/bin/env python
# coding: utf8
"""
Importer data collected from government websites to the opendata hub
"""
import ckanclient
import csv
import json
import hashlib
API_KEY_FILENAME = "apikey.txt"

API_URL = "http://datahub.opengovdata.ru/api"
DATASETS_FILENAME = 'data/processed_websites.csv'


class DataImporter:
    """Data importer class for data.mos.ru"""
    def __init__(self):
        self.apikey = open(API_KEY_FILENAME).read()
        self.ckan = ckanclient.CkanClient(base_location=API_URL, api_key=self.apikey)
        self.package_list = self.ckan.package_register_get()
        self.started = True
        self.start_key = ''
        pass

    def import_all(self):
        """Processes all data from twitters.csv and creates package"""
        reader = csv.DictReader(open(DATASETS_FILENAME, 'r'), delimiter="\t")
        package_names = []
        for package in reader:
            package_names.append(self.register(package))
        self.update_group('govnews', package_names)
        pass

    def register(self, package):
        """Register or update dataset
        :param package:
        """
        id = hashlib.sha1(package['feedurl']).hexdigest().encode('utf-8')[0:8]
        key = 'feed_' + id.lower()
        if not self.started:
            if key != self.start_key:
                print 'Already imported. Skipping'
                return key
            else:
                self.started = True
        filename = '%s.csv' % id

        try:
            r = self.ckan.package_entity_get(key)
            status = 0

        except ckanclient.CkanApiNotFoundError, e:
            status = 404
        tags = [u'новости', u'RSS', u'официально', u'госсайты']
        feedtype = 'RSS' if package['feedtype'] == 'undefined' else package['feedtype'].upper()

        name = feedtype + u' лента от ' + package['name'].decode('utf8')+ u' (%s - %s)' %(package['title'].decode('utf8'), package['feedurl'])
        description = u'Новостная лента от ' + package['name'].decode('utf8') + u' (%s - %s)' %(package['title'].decode('utf8'), package['feedurl'])
        resources = [{'name': package['title'] if len(package['title']) > 0 else u"Новостная лента", 'format': feedtype, 'url': package['feedurl'],
                      'description': description},
                     ]


        print name

        the_package = { 'name' : key, 'title' : name,
                           'notes' :  description.encode('utf8'),
                           'tags' : tags,
                           'state' : 'active',
                           'resources': resources,
                           'author' : 'Ivan Begtin',
                           'author_email' : 'ibegtin@infoculture.ru',
                           'maintainer' : 'Ivan Begtin',
                           'maintainer_email' : 'ibegtin@infoculture.ru',
                           'license_id' : 'other-nc',
                           'owner_org': "",
                           'extras': package
                        }
#            self.ckan.package_entity_update(package)
#
#        if True:
        if status == 404:
            try:
                self.ckan.package_register_post(the_package)
            except Exception, e:
                print 'Error importing', key
                print e, type(e), e.message
                return key
                pass
            print "Imported", key
        else:
            package_entity = self.ckan.last_message
            if type(package_entity) == type(''): return None
            package_entity.update(the_package)
            for k in ['id', 'ratings_average', 'relationships', 'ckan_url', 'ratings_count']:
                del package_entity[k]
            self.ckan.package_entity_put(package_entity)
            print "Updated", key
#            print self.ckan.last_message
        return key

    def update_group(self, group_name, package_names, group_title="", description=""):
            #        print key
            try:
                group = self.ckan.group_entity_get(group_name)
                status = 0
            except ckanclient.CkanApiNotFoundError, e:
                status = 404
            if status == 404:
                group_entity = {'name' : group_name, 'title' : group_title, 'description' : description }
                self.ckan.group_register_post(group_entity)
            group = self.ckan.group_entity_get(group_name)
            for name in package_names:
                if name not in group['packages']:
                    group['packages'].append(name)
            self.ckan.group_entity_put(group)


if __name__ == "__main__":
    imp = DataImporter()
#    imp.collect_data()
#    imp.delete_all()
    imp.import_all()