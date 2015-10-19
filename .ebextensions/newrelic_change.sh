/bin/sed s/\$NEW_RELIC_APP_NAME/"${1}"/g ./newrelic_sample.ini > ./newrelic.ini
chown -R wsgi:wsgi ./newrelic.ini
/bin/rm ./newrelic_sample.ini
