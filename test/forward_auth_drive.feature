Feature: Reverse (query-based) authorization for MongoDB

  This feature tests Data Filtering (https://www.osohq.com/docs/oss/guides/data_filtering.html) for the MongoDB
  Oso adapter, which transform authorization rules into filtering conditions that allow the application to, for
  example, answer the question "Which documents is Jane allowed to edit?", answered with a list of documents
  (in contrast to direct/forward authentication, where the question is "Can Jane edit this specific document?",
  which is instead answered with simply Yes/No)

  Background:
    Given the Polar file test/drive.polar

  # All these examples come from the built-in tests at the end of https://github.com/osohq/sample-apps-node/blob/main/oso-drive/scripts/main.polar

  #test "can write folder and contents if file owner" {
  #    setup {
  #        has_relation(File{"tps-reports/tps-report-1999.txt"}, "owner", User{"Peter"});
  #    }
  #
  #    assert allow(User{"Peter"}, "write", File{"tps-reports/tps-report-1999.txt"});
  #    assert_not allow(User{"Michael"}, "write", File{"tps-reports/tps-report-1999.txt"});
  #}
  Example: can write folder and contents if file owner
    Given a file tps-reports/tps-report-1999.txt owned by Peter
    Then Peter can write file tps-reports/tps-report-1999.txt
    And Michael cannot write file tps-reports/tps-report-1999.txt

  #test "can write folder and contents if folder owner" {
  #    setup {
  #        has_relation(Folder{"tps-reports"}, "owner", User{"Bill"});
  #        has_relation(File{"tps-reports/tps-report-1999.txt"}, "folder", Folder{"tps-reports"});
  #        has_relation(File{"payroll/office-expenses.txt"}, "folder", Folder{"payroll"});
  #    }
  #
  #    assert allow(User{"Bill"}, "write", File{"tps-reports/tps-report-1999.txt"});
  #    assert allow(User{"Bill"}, "write", Folder{"tps-reports"});
  #    assert_not allow(User{"Peter"}, "write", Folder{"tps-reports"});
  #}
  Example: can write folder and contents if folder owner
    Given a Folder tps-reports owned by Bill
    And a File tps-reports/tps-report-1999.txt stored in folder tps-reports
    And a File payroll/office-expenses.txt stored in folder payroll
    Then Bill can write file tps-reports/tps-report-1999.txt
    And Bill can write folder tps-reports
    And Peter cannot write folder tps-reports

  #test "can read folder if member of org and folder is readable by org" {
  #    setup {
  #        has_role(User{"Samir"}, "member", Organization{"Initech"});
  #        has_relation(Folder{"tps-reports"}, "organization", Organization{"Initech"});
  #        has_relation(Folder{"payroll"}, "organization", Organization{"Initech"});
  #        is_readable_by_org(Folder{"tps-reports"});
  #    }
  #
  #    assert allow(User{"Samir"}, "read", Folder{"tps-reports"});
  #    assert_not allow(User{"Samir"}, "read", Folder{"payroll"});
  #}
  Example: can read folder if member of org and folder is readable by org
    Given that user Samir is a member of Initech
    And a folder tps-reports owned by org Initech
    And a folder payroll owned by org Initech
    And that folder tps-reports is org-readable
    Then Samir can read folder tps-reports
    Then Samir cannot read folder payroll

  #test "can read file if member of org and folder is readable by org" {
  #    setup {
  #        has_role(User{"Samir"}, "member", Organization{"Initech"});
  #        has_relation(Folder{"tps-reports"}, "organization", Organization{"Initech"});
  #        has_relation(Folder{"payroll"}, "organization", Organization{"Initech"});
  #        is_readable_by_org(Folder{"tps-reports"});
  #        has_relation(File{"tps-reports/tps-report-1999.txt"}, "folder", Folder{"tps-reports"});
  #        has_relation(File{"payroll/office-expenses.txt"}, "folder", Folder{"payroll"});
  #    }
  #
  #    assert allow(User{"Samir"}, "read", File{"tps-reports/tps-report-1999.txt"});
  #    assert_not allow(User{"Samir"}, "read", File{"payroll/office-expenses.txt"});
  #}
  Example: can read file if member of org and folder is readable by org
    Given that user Samir is a member of Initech
    And a Folder tps-reports owned by org Initech
    And a folder payroll owned by org Initech
    And that folder tps-reports is org-readable
    And a File tps-reports/tps-report-1999.txt stored in folder tps-reports
    And a file payroll/office-expenses.txt stored in folder payroll
    Then Samir can read file tps-reports/tps-report-1999.txt
    Then Samir cannot read file payroll/office-expenses.txt

  #test "can read public file" {
  #    setup {
  #        is_public(File{"test.txt"});
  #    }
  #
  #    assert allow(User{"Samir"}, "read", File{"test.txt"});
  #    assert_not allow(User{"Samir"}, "read", File{"text2.txt"});
  #    assert_not allow(User{"Samir"}, "write", File{"text.txt"});
  #}
  Example: can read public file
    Given that file text.txt is public
    Then Samir can read file text.txt

  #test "roles on folders bubble down to files in subfolders" {
  #    setup {
  #        has_role(User{"Samir"}, "reader", Folder{"tps-reports"});
  #        has_relation(Folder{"tps-reports/1999"}, "folder", Folder{"tps-reports"});
  #        has_relation(File{"tps-reports/1999/peter.txt"}, "folder", Folder{"tps-reports/1999"});
  #    }
  #
  #    assert allow(User{"Samir"}, "read", Folder{"tps-reports"});
  #    assert allow(User{"Samir"}, "read", Folder{"tps-reports/1999"});
  #    assert allow(User{"Samir"}, "read", File{"tps-reports/1999/peter.txt"});
  #    assert_not allow(User{"Samir"}, "read", Folder{"payroll"});
  #}
  Example: roles on folders bubble down to files in subfolders
    Given that user Samir is a reader of folder tps-reports
    And a folder tps-reports/1999 stored inside tps-reports
    And a file tps-reports/1999/peter.txt stored in folder tps-reports/1999
    Then Samir can read folder tps-reports
    And Samir can read folder tps-reports/1999
    And Samir can read file tps-reports/1999/peter.txt
    And Samir cannot read folder payroll