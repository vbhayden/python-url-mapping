from requests import Request, Response, Session, get
from bs4 import BeautifulSoup

# Keep a session going
session = Session()

# Common extensions used by attachments
extensions = ['.alx', '.asp', '.au', '.avi', '.bas', '.bat', '.bin', '.bmp', '.c', '.cab', '.cda', '.cdr', '.chf',
              '.cmd', '.com', '.cpl', '.cur', '.dic', '.dll', '.doc', '.dot', '.drw', '.dwg', '.dxf', '.eml', '.eps',
              '.exe', '.fav', '.gif', '.grp', '.gtar', '.gwf', '.gz', '.hlp', '.ht', '.htm', '.html', '.ico', '.img',
              '.inf', '.ini', '.iso', '.java', '.jpeg', '.jpg', '.js', '.jse', '.ldb', '.lnk', '.log', '.mdb', '.mde',
              '.mdw', '.mid', '.midi', '.mov', '.movie', '.mp1', '.mp2', '.mp3', '.mpeg', '.mpg', '.msg', '.msi',
              '.msp', '.nws', '.obd', '.oft', '.pbk', '.pcl', '.pcx', '.pdd', '.pdf', '.pic', '.pif', '.pl', '.pot',
              '.pps', '.ppt', '.pub', '.qbb', '.qbw', '.qdb', '.ra', '.reg', '.scr', '.sct', '.shtml', '.snd', '.sys',
              '.tar', '.text', '.tga', '.tgz', '.tif', '.tsv', '.ttf', '.txt', '.url', '.uu', '.vbe', '.vbs', '.vir',
              '.wav', '.wb2', '.wbk', '.wiz', '.wk4', '.wks', '.wma', '.wmf', '.wpd', '.wri', '.wsc', '.wsf', '.wsh',
              '.xlk', '.xls', '.xlt', '.xml', '.z', '.zip']


def get_soup(url) -> (BeautifulSoup, int):
    """
    Returns the soup'ed page content at the given URL.

    :param url: URL we're checking.
    :return: BeautifulSoup instance, response status code as an int
    """
    response = get(url)
    return BeautifulSoup(response.content, "lxml"), response.status_code


def is_attachment(url):
    """
    Check if this URL is pointing at an attachment.

    :param url: URL to check.
    :return: Whether this is likely an attachment.
    """

    trimmed = url.strip()

    for extension in extensions:
        if trimmed.endswith(extension) or trimmed.endswith(extension + "x"):
            return True

    return False


def search_all_urls(parent_root: str, save=False, verbose=False) -> dict:
    """
    Hunt down every link accessible on a page, mapping the available links and returning a dictionary
    with each of those links, what they can access, and what can access them.

    :param parent_root: Root page
    :param save: Save the information to csv / json.
    :param verbose: Prints output for each of the URLs checked.
    :return:
    """

    def is_local(href) -> bool:
        """
        Check if the given HREF is a local path within the site.

        :param href: HREF within some HTML element.
        :return: Whether or not this is local.
        """
        return (len(href) > 0 and href[0] == "/") or href == parent_url

    def register_link(href: str):
        """
        Assigns the HREF to its appropriate section within the dictionary.

        :param href: HREF to check.
        :return: None.
        """
        if "http" in href:
            links["external"].append(href)
            return False
        elif is_attachment(href):
            links["attachments"].append(href)
            return False
        elif len(href) > 0 and href[0] == "/":
            links["local"].append(href)
            return True
        else:
            links["misc"].append(href)
            return False

    def update_refs(current_page_href, href_on_page):
        """
        Updates the Forward / Backward maps based on the HREF we found on the current page and the
        HREF we used to reach that current page.

        :param current_page_href: HREF of page we're currently on.
        :param href_on_page: HREF we found on that current page.
        :return: None.
        """
        # Forward and Backward refs are dictionaries, so we'll check if the urls are already
        # here.  If not, we'll need to add a new list to store everything.
        #
        # For Forward refs,  this dictionary maps a url to every other url it referenced.
        #
        # For Backward refs, this dictionary maps a url to a list of other urls that were found
        # to reference it.
        #
        if current_page_href not in links["forward_refs"]:
            links["forward_refs"][current_page_href] = []

        # We don't care about backward references unless the url is a local page OR an attachment.
        #
        if href_on_page not in links["backward_refs"] and (is_local(href_on_page) or is_attachment(href_on_page)):
            links["backward_refs"][href_on_page] = []

        # Make sure we're only logging LOCAL pages or ATTACHMENTS.  Misc stuff and external pages don't really
        # matter for this effort as we don't maintain those.
        #
        if is_local(href_on_page) or is_attachment(href_on_page):
            if href_on_page not in links["forward_refs"][current_page_href]:
                links["forward_refs"][current_page_href].append(href_on_page)

        # We're only concerned with local pages referencing other local documents
        #
        if current_page_href in links["local"] and (is_local(href_on_page) or is_attachment(href_on_page)):
            if current_page_href not in links["backward_refs"][href_on_page]:
                links["backward_refs"][href_on_page].append(current_page_href)

    def trim_url(raw_url: str) -> str:
        """
        Removes the HTTP / HTTPS chunks from the start of a URL.

        :param raw_url: URL to trim.
        :return: Trimmed URL.
        """
        trimmed = raw_url.replace("https://www.", "").replace("http://www.", "")
        trimmed = trimmed.replace("https://", "").replace("http://", "")
        return trimmed

    def clean_link(href: str) -> str:
        """
        Cleans the HREF and replaces links to the parent url.  Most of the time, this will just be
        removing the starting "/" character.

        :param href: HREF to clean.
        :return: Cleaned version of the HREF.
        """
        clean = (href[:-1] if "/" == href[-1] else href).lower()

        # Clear out http and https
        clean_parent = trim_url(parent_root)
        clean = trim_url(clean)

        # Remove the parent URL
        if clean_parent in clean:
            clean = clean[len(clean_parent):]

        return clean

    def get_links(href, skip_headers=False) -> (list, int):
        """
        Returns a list of all links accessible from the given HREF / URL.

        :param href:
        :param skip_headers:
        :return:
        """

        # We might need to make this a fully qualified URL
        target_url = href if "http" in href else parent_url + href
        soup, response_code = get_soup(target_url)

        # Convert this into a string
        str_soup = str(soup)

        # Clear the header and footer
        if skip_headers:
            for div in soup.find_all("div", id="top_section"):
                div.decompose()
            for div in soup.find_all("div", id="footer_section"):
                div.decompose()

        # Missing page errors
        if "404:" in str_soup or 400 <= response_code <= 499:
            return [], 404

        # Server errors and problems with missing page components
        if "505:" in str_soup or "[error]" in str_soup.lower() or 500 <= response_code <= 599:
            return [], 500

        # Sometimes the <a> elements can be strange, so be careful here
        try:
            # Return a list of clean HREFs for every <a> element we have, as long as those <a> elements
            # actually have a valid HREF.
            #
            return [clean_link(a["href"])
                    for a in soup.find_all("a")
                    if a.has_attr("href") and len(a["href"]) > 0], 200

        except Exception as ex:
            print("{0} :: {1}".format(href, ex))
            return [], 200

    def print_group(key: str, group_name: str):
        """
        Print a given group we've collected during the process.

        :param key: Exact key name for the links
        :param group_name: Group name to display
        :return: None (prints to console).
        """
        print("{0} ({1}):".format(group_name, len(links[key])))
        for href in links[key]:
            print("-" + href)
        print("")

    # Clean the parent URL a bit before we continue.
    parent_url = parent_root[:-1] if parent_root.endswith("/") else parent_root

    # Keep track of which links we've already checked and which ones are in line.
    checked = []
    pending = [parent_url]

    # This is the object we're returning.  It's a dictionary mapping various URLs
    # to matching arrays.
    links = {
        "local": [],
        "external": [],
        "misc": [],
        "404": [],
        "500": [],
        "attachments": [],
        "forward_refs": {},
        "backward_refs": {}
    }

    # Go until we're out of links to check
    while len(pending) > 0:

        # Get the next link in line.  By default, we
        url = pending[0]

        # Add this to our json object and check if it was local to the page
        should_check = register_link(url) or url == parent_url

        # If it's weird or external, ignore it
        if should_check:

            # Get every link on this page
            page_urls, code = get_links(url, url != parent_url)

            if code == 200:
                for page_url in page_urls:

                    # Update who was looking at who
                    update_refs(url, page_url)

                    # Bookkeeping
                    if page_url in checked:
                        continue
                    if page_url in pending:
                        continue

                    # Don't do this for absolute, external urls
                    if "http" not in page_url:
                        pending.append(page_url)

            # Check if this was an actual page
            if code == 404:
                links["404"].append(url)

            if code == 500:
                links["500"].append(url)

        # We've now checked this url
        checked.append(url)
        while url in pending:
            pending.remove(url)

        # Print progress
        if verbose:
            print("{0} pending, {1} checked ({2} local, {3} ext, {4} misc, {5} 404s, {6} 500s)".format(
                len(pending), len(checked), len(links["local"]), len(links["external"]),
                len(links["misc"]), len(links["404"]), len(links["500"])
            ), end="")

            print("..." + url)

    # Sort these once we're done
    links["local"].sort()
    links["attachments"].sort()
    links["external"].sort()
    links["404"].sort()
    links["500"].sort()

    count404 = len(links["404"])
    count500 = len(links["500"])

    # # Print what we found
    if count404 == 0 and count500 == 0:
        print("... no 404 or 500 codes reported.  Site looks fine!")

    if count500 != 0:
        print("{0} 500 codes returned:".format(count500))
        print_group("500", "500's")

    if count404 != 0:
        print("{0} 404 codes returned:".format(count500))
        print_group("404", "404's")

    if save:
        save_json(links, name="results.json")
        save_csv(links, name="results.csv")

    return links


def save_json(raw: dict, name: str):
    """
    Save the data to JSON.

    :param raw: Dictionary of results.
    :param name: File name / path to use.
    :return: None.
    """

    import json
    with open(name, "w+") as f:
        json_str = json.dumps(raw, indent=4, sort_keys=True)
        f.write(json_str)

    print("saved JSON data to " + name)


def save_csv(raw: dict, name: str):
    """
    Save the data to CSV.

    :param raw: Dictionary of results.
    :param name: File name / path to use.
    :return: None.
    """
    csv = ""

    for key in raw["forward_refs"]:
        block = "\n".join(key + ",links_to," + ref for ref in raw["forward_refs"][key])
        csv += block + "\n"
    for key in raw["backward_refs"]:
        block = "\n".join(key + ",links_from," + ref for ref in raw["backward_refs"][key])
        csv += block + "\n"

    with open(name, "w+") as f:
        f.write(csv)

    print("saved CSV data to " + name)


def show_help():
    """
    Show the commands to the user.

    :return: None (prints to console).
    """

    def print_help_item(arg, display):
        print("{0: <12} {1}".format(arg, display))

    print("Available Arguments:")
    print("=" * 30)

    print_help_item("--help", "Displays all argument options")
    print_help_item("--save", "Saves the results with the default names")
    print_help_item("--verbose", "Prints updates as each URL is checked.")

    print("=" * 30)


def main(args):

    if "--help" in args:
        show_help()
        return

    # We need arguments to run this
    if len(args) > 1:

        # Get the URL to check
        url_to_check = args[1]

        # Args
        should_save = "--save" in args
        be_verbose = "--verbose" in args

        if not be_verbose:
            print("Starting URL map for " + url_to_check + " ... ")

        # Check if we should save this
        search_all_urls(parent_root=url_to_check, save=should_save, verbose=be_verbose)

    else:
        print("You must provide a URL as the first argument.")


if __name__ == '__main__':

    import sys
    main(sys.argv)

