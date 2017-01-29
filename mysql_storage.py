#!/usr/bin/python
# coding: utf-8

import logging

import MySQLdb


class MysqlStorage:
    def __init__(self, host, user, password, database):
        self.log = logging.getLogger("MysqlStorage")

        self.log.info("Connecting mysql, host=%s, user=%s, database=%s",
                      host, user, database)
        self.db = MySQLdb.connect(host, user, password, database)

    def insert_house_list(self, house_list):
        # TODO(sghao): Re-write house list insertion logic in the same way as
        # house detail insertion logic, i.e. using dictionary to pass around
        # schemaful object, rather than an array of schemaless object, relying
        # on consistent interpretation in different circumstances.
        self.log.info("Inserting house list into mysql, len(house_list)=%d.",
                      len(house_list))

        cursor = self.db.cursor()
        new_house_count = 0
        for house in house_list:
            insert_statement = self._get_insert_house_statements(house)
            result = cursor.execute(insert_statement)
            if result == 0:
                self.log.info("Duplicate house, ignored: %d", house[0])
            elif result == 1:
                new_house_count += 1
                self.log.info("Successfully inserted house: %d", house[0])
            else:
                self.log.fatal(
                    "Unexpected result while inserting house: %d, %d",
                    house[0], result)

        self.db.commit()
        self.log.info("Committed %d new house into house list.",
                      new_house_count)

    def _get_insert_house_statements(self, house):
        return """
            INSERT IGNORE INTO house_list(
                verification_id,
                district,
                compound_name,
                house_layout,
                house_area,
                proposed_price,
                agency,
                date,
                house_id)
            VALUES (%s, '%s', '%s', '%s', %s, %s, '%s', '%s', %s)
        """ % tuple(house)

    def insert_house_detail(self, house_detail):
        self.log.info("Inserting house detail: house_id=%d",
                      house_detail["house_id"])

        sql = self._get_insert_statement(
            table="house_detail",
            ignore_duplicate=True,
            column_values=house_detail)

        cursor = self.db.cursor()
        result = cursor.execute(sql)

        house_id = house_detail["house_id"]
        if result == 0:
            self.log.info("Ignored duplicate house: house_id=%d", house_id)
        elif result == 1:
            self.log.info(
                "Successfully inserted house into house_detail: house_id=%d",
                house_id)
        else:
            self.log.fatal(
                "Unexpected result while inserting house into house_detail: "
                "%d, %d", house_id, result)

        self.db.commit()

    def _get_insert_statement(
            self, table, column_values, ignore_duplicate=False):
        columns = ", ".join(column_values.keys())
        values = ", ".join([
            "'%s'" % v if isinstance(v, str) else "%s" % v
            for v in column_values.values()])
        ignore_duplicate_str = "IGNORE" if ignore_duplicate else ""

        return """
            INSERT %(ignore_duplicate_str)s INTO %(table)s(
                %(columns)s
            )
            VALUES (
                %(values)s
            )
        """ % locals()
