#!/usr/bin/python
# coding: utf-8

import MySQLdb


class MysqlStorage:
    def __init__(self, host, user, password, database):
        self.db = MySQLdb.connect(host, user, password, database)

    def insert_house_list(self, house_list):
        insert_statements = [self._get_insert_house_statements(house)
                for house in house_list]

        # TODO(sghao): Maybe print some log about how many houses are
        # successfully inserted.
        cursor = self.db.cursor()
        [cursor.execute(sql) for sql in insert_statements]
        self.db.commit()

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
