#
# This is 2012.1 essex-4 milestone snapshot
#
%global release_name essex
%global release_letter e
%global milestone 4
%global snapdate 20120229
%global git_revno r2059
%global snaptag ~%{release_letter}%{milestone}~%{snapdate}.%{git_revno}

Name:           openstack-keystone
Version:        2012.1
Release:        0.10.%{release_letter}%{milestone}%{?dist}
Summary:        OpenStack Identity Service

License:        ASL 2.0
URL:            http://keystone.openstack.org/
Source0:        http://launchpad.net/keystone/%{release_name}/%{release_name}-%{milestone}/+download/keystone-%{version}~%{release_letter}%{milestone}.tar.gz
#Source0:        http://keystone.openstack.org/tarballs/keystone-%{version}%{snaptag}.tar.gz
Source1:        openstack-keystone.logrotate
Source2:        openstack-keystone.service
Source3:        openstack-keystone-db-setup
Source4:        openstack-config-set
Source5:        sample_data.sh

# https://review.openstack.org/4658
# https://review.openstack.org/5049
Patch1:         sample_data.sh-catalog-backend.patch
# https://review.openstack.org/4997
Patch2:         add-more-default-catalog-templates.patch

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-sphinx >= 1.1.2
BuildRequires:  python-iniparse
BuildRequires:  systemd-units

Requires:       python-keystone = %{version}-%{release}
Requires:       python-keystoneclient >= 2012.1-0.4.e4

Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units
Requires(pre):    shadow-utils

%description
Keystone is a Python implementation of the OpenStack
(http://www.openstack.org) identity service API.

This package contains the Keystone daemon.

%package -n       python-keystone
Summary:          Keystone Python libraries
Group:            Applications/System
# python-keystone added in 2012.1-0.2.e3
Conflicts:      openstack-keystone < 2012.1-0.2.e3

Requires:       python-crypto
Requires:       python-dateutil
Requires:       python-eventlet
Requires:       python-httplib2
Requires:       python-ldap
Requires:       python-lxml
Requires:       python-memcached
Requires:       python-migrate
Requires:       python-paste
Requires:       python-paste-deploy
Requires:       python-paste-script
Requires:       python-prettytable
Requires:       python-routes
Requires:       python-sqlalchemy
Requires:       python-webob
Requires:       python-passlib
Requires:       MySQL-python

%description -n   python-keystone
Keystone is a Python implementation of the OpenStack
(http://www.openstack.org) identity service API.

This package contains the Keystone Python library.

%prep
%setup -q -n keystone-%{version}
%patch1 -p1
%patch2 -p1

# change default configuration
%{SOURCE4} etc/keystone.conf DEFAULT log_file %{_localstatedir}/log/keystone/keystone.log
%{SOURCE4} etc/keystone.conf sql connection mysql://keystone:keystone@localhost/keystone
%{SOURCE4} etc/keystone.conf catalog template_file %{_sysconfdir}/keystone/default_catalog.templates
%{SOURCE4} etc/keystone.conf catalog driver keystone.catalog.backends.sql.Catalog
%{SOURCE4} etc/keystone.conf identity driver keystone.identity.backends.sql.Identity
%{SOURCE4} etc/keystone.conf token driver keystone.token.backends.sql.Token
%{SOURCE4} etc/keystone.conf ec2 driver keystone.contrib.ec2.backends.sql.Ec2

find . \( -name .gitignore -o -name .placeholder \) -delete
find keystone -name \*.py -exec sed -i '/\/usr\/bin\/env python/d' {} \;


%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root %{buildroot}

# Delete tests
rm -fr %{buildroot}%{python_sitelib}/tests
rm -fr %{buildroot}%{python_sitelib}/run_tests.*

install -d -m 755 %{buildroot}%{_sysconfdir}/keystone
install -p -D -m 640 etc/keystone.conf %{buildroot}%{_sysconfdir}/keystone/keystone.conf
install -p -D -m 640 etc/default_catalog.templates %{buildroot}%{_sysconfdir}/keystone/default_catalog.templates
install -p -D -m 640 etc/policy.json %{buildroot}%{_sysconfdir}/keystone/policy.json
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-keystone
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/openstack-keystone.service
# Install database setup helper script.
install -p -D -m 755 %{SOURCE3} %{buildroot}%{_bindir}/openstack-keystone-db-setup
# Install sample data script.
install -p -D -m 755 %{SOURCE5} %{buildroot}%{_bindir}/openstack-keystone-sample-data
# Install configuration helper script.
install -p -D -m 755 %{SOURCE4} %{buildroot}%{_bindir}/openstack-config-set

install -d -m 755 %{buildroot}%{_sharedstatedir}/keystone
install -d -m 755 %{buildroot}%{_localstatedir}/log/keystone

# docs generation requires everything to be installed first
export PYTHONPATH="$( pwd ):$PYTHONPATH"
pushd docs
make html
popd
# Fix hidden-file-or-dir warnings
rm -fr docs/build/html/.doctrees docs/build/html/.buildinfo

%pre
getent group keystone >/dev/null || groupadd -r keystone
getent passwd keystone >/dev/null || \
useradd -r -g keystone -d %{_sharedstatedir}/keystone -s /sbin/nologin \
-c "OpenStack Keystone Daemons" keystone
exit 0

%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable openstack-keystone.service > /dev/null 2>&1 || :
    /bin/systemctl stop openstack-keystone.service > /dev/null 2>&1 || :
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart openstack-keystone.service >/dev/null 2>&1 || :
fi

%files
%doc LICENSE
%doc README.rst
%doc docs/build/html
%{_bindir}/keystone-all
%{_bindir}/keystone-manage
%{_bindir}/openstack-config-set
%{_bindir}/openstack-keystone-db-setup
%{_bindir}/openstack-keystone-sample-data
%{_unitdir}/openstack-keystone.service
%dir %{_sysconfdir}/keystone
%config(noreplace) %attr(640, root, keystone) %{_sysconfdir}/keystone/keystone.conf
%config(noreplace) %attr(640, root, keystone) %{_sysconfdir}/keystone/default_catalog.templates
%config(noreplace) %attr(-, keystone, keystone) %{_sysconfdir}/keystone/policy.json
%config(noreplace) %{_sysconfdir}/logrotate.d/openstack-keystone
%dir %attr(-, keystone, keystone) %{_sharedstatedir}/keystone
%dir %attr(-, keystone, keystone) %{_localstatedir}/log/keystone

%files -n python-keystone
%defattr(-,root,root,-)
%doc LICENSE
%{python_sitelib}/keystone
%{python_sitelib}/keystone-%{version}-*.egg-info

%changelog
* Thu Mar 08 2012 Dan Prince <dprince@redhat.com> 2012.1-0.10.e4
- install etc/policy.json config file

* Thu Mar 08 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.10.e4
- change default catalog backend to sql rhbz#800704
- update sample-data script
- add missing keystoneclient dependency

* Thu Mar 01 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.9.e4
- essex-4 milestone

* Sat Feb 25 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.8.e4
- change default database to mysql

* Tue Feb 21 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.7.e4
- switch all backends to sql

* Mon Feb 20 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.6.e4
- add missing default_catalog.templates

* Mon Feb 20 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.5.e4
- pre essex-4 snapshot, for keystone rebase

* Mon Feb 13 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.4.e3
- fix deps rhbz#787072
- keystone is not hashing passwords lp#924391
- Fix "KeyError: 'service-header-mappings'" lp#925872

* Wed Feb  8 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 2012.1-0.3.e3
- Remove the dep on python-sqlite2 as that's being retired in F17 and keystone
  will work with the sqlite3 module from the stdlib

* Thu Jan 26 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.2.e3
- separate library to python-keystone
- avoid conflict with python-keystoneclient

* Thu Jan 26 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.1.e3
- essex-3 milestone

* Wed Jan 18 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.e2
- essex-2 milestone

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2011.3.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Nov 24 2011 Alan Pevec <apevec@redhat.com> 2011.3.1-2
- include LICENSE, update package description from README.md

* Mon Nov 21 2011 Alan Pevec <apevec@redhat.com> 2011.3.1-1
- Update to 2011.3.1 stable/diablo release

* Fri Nov 11 2011 Alan Pevec <apevec@redhat.com> 2011.3-2
- Update to the latest stable/diablo snapshot

* Mon Oct 24 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-1
- Update version to diablo final

* Wed Oct 19 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.4.d4.1213
- add Requires: python-passlib

* Mon Oct 3 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.2.d4.1213
- update to diablo release.
- BR systemd-units for _unitdir

* Fri Sep  2 2011 Mark McLoughlin <markmc@redhat.com> - 1.0-0.2.d4.1078
- Use upstream snapshot tarball
- No need to define python_sitelib anymore
- BR python2-devel
- Remove BRs only needed for unit tests
- No need to clean buildroot in install anymore
- Use slightly more canonical site for URL tag
- Prettify the requires tags
- Cherry-pick tools.tracer patch from upstream
- Add config file
- Add keystone user and group
- Ensure log file is in /var/log/keystone
- Ensure the sqlite db is in /var/lib/keystone
- Add logrotate support
- Add system units

* Thu Sep  1 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.1.20110901git396f0bfd%{?dist}
- initial packaging
