#
# Author : Thamme Gowda <tgowdan@gmail.com>
# Date: September 14, 2016
import requests
import logging
from lxml import etree

class XTree(object):
    '''
        A wraper tree for the sake of convenience with XPath extractions
    '''
    def __init__(self, tree):
        self.tree = tree

    def string(self, expr, idx=0):
        ss = self.tree.xpath(expr)
        return ss[idx] if ss and idx < len(ss) else None

    def strings(self, expr):
        return self.tree.xpath(expr)

    def joinedstring(self, expr, delim='\n'):
        return delim.join(self.tree.xpath(expr))

    def date(self, expr):
        #TODO: Parse date
        return self.string(expr)

    def elements(self, expr):
        return self.tree.xpath(expr)

class LinkedInProfileScraper(object):
    """
        Scraper for Linked IN Public profile
    """
    HEADERS = {
        'DNT': '1',
        'Accept-Encoding': 'deflate, sdch, br',
        'Accept-Language': 'en-US,en;q=0.8,kn;q=0.6',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    def scrape_profile(self, profile_url):
        logging.info("Scraping %s" % profile_url)
        response = requests.get(profile_url, headers=LinkedInProfileScraper.HEADERS)
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
        tree = XTree(etree.HTML(response.text))
        profile = {}

        # Parse basic info
        self.parse_basic(tree, profile)

        # parse positions/experience
        posits = tree.elements('//section[@id="experience"]//*[@data-section="currentPositionsDetails" or @data-section="pastPositionsDetails"]')
        profile['positions'] = [self.parse_position(XTree(p)) for p in posits]
        voluntees = tree.elements('//*[@data-section="volunteering"]//li[@class="position"]')
        profile['volunteer_positions'] = [self.parse_volunteer_position(XTree(p)) for p in voluntees]
        # TODO: Parse Projects
        return profile

    def parse_basic(self, root, profile):
        profile['title'] = root.string('//h1[@id="name"]/text()')
        profile['headline'] = root.string('//*[@data-section="headline"]/text()')
        profile['locality'] = root.string('//*[@class="locality"]/text()')
        profile['industry'] = root.string('//*[@class="descriptor"]/text()')
        profile['current_orgs'] = root.strings('//*[@data-section="currentPositionsDetails"]/td//a/text()')
        profile['past_orgs'] = root.strings('//*[@data-section="pastPositionsDetails"]/td//a/text()')
        profile['education_orgs'] = root.strings('//*[@data-section="educationsDetails"]/td//a/text()')
        profile['summary'] = root.joinedstring('//*[@data-section="summary"]//p/text()')
        profile['skills'] = root.strings('//li[contains(@class, "skill") and not(contains(@class, "see"))]//text()')

    def parse_position(self, root):
        return {
            'role': root.string('.//header//*[@class="item-title"]//text()'),
            'oraganization': root.string('.//header//*[@class="item-subtitle"]//a/text()'),
            'start_date': root.date('.//time[1]/text()'),
            'end_date': root.date('.//time[2]/text()'),
            'description': root.joinedstring('.//p[@class="description"]//text()')
        }

    def parse_volunteer_position(self, root):
        pos = self.parse_position(root)
        pos['cause'] = root.string('.//*[@class="cause"]//text()')
        return pos

if __name__ == "__main__":
    import sys, json
    scraper = LinkedInProfileScraper()
    if len(sys.argv) != 2:
        print("Usage %s https://www.linkedin.com/in/<username>" % sys.argv[0])
        sys.exit(1)
    url = sys.argv[1]
    profile = scraper.scrape_profile(url)
    print(json.dumps(profile, indent=2))
