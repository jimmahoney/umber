----------------------------------------
-- umber_db.sql
--
--   umber database definitions for sqlite3 database
--
--       Person
--       Role	
--       Course
--       Registration        FK Person, FK Course, FK Role
--       Assignment          FK Course
--       Work 		     FK Person, FK Assignment 
--       Directory           FK Course, FK Parent
--       Permission          FK Directory, FK Role, FK Person
--
--   To create the database :          ./init_db
--   To create & populate it:          ./reset_db
--   To create an ERD diagram of it:   ./erd/make_png
--
-- Authentication of users can be from an LDAP database, 
-- which is the default on the Marlboro College campus.
-- In that case, password here is left blank, and the rest 
-- is mostly a duplicate of the info there.
--    here       ldap
--    ----       ----
--    ldap_id    uidNumber
--    username   uid
-- Otherwise, this password provides an alternate authentication
-- mechanism, via a mechanism specified in the 'crypto' filed.
-- If crypto is null, then the password is simply stored in plaintext.
-- If its value is 'crypt', then its encrypted with the
-- standard unix/perl 'crypt' function.
-- The (name, firstname, lastname) are redundant, but I've left all of
-- 'em here for some flexibility, and to allow sorting by last name
-- even while allowing for nicknames in the "name" field, e.g.
--    username   csmith
--    firstname  Christopher
--    lastname   Smith
--    name       Topher Smith
-- Keeping 'em is also consistent with the ldap, which has
-- (cn sn displayname) as (firstname lastname name).
-- My intention is to use "lastname, firstname" as the more
-- formal name and something more casual as "name".
-- If not provided, the email is assumed to be username@domain, 
-- e.g. csmith@marlboro.edu
--
CREATE TABLE Person (
  person_id INTEGER PRIMARY KEY NOT NULL,
  ldap_id INTEGER NOT NULL DEFAULT 0,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL DEFAULT '',
  crypto TEXT NOT NULL DEFAULT '',
  name TEXT NOT NULL DEFAULT '',
  email TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT ''
);

-- Speed selects at the cost of slowing table modifications.
CREATE UNIQUE INDEX person_username_index ON Person (username);
CREATE INDEX person_ldap_index ON Person (ldap_id);

--
-- The status roles are (in order of ascending privileges)
-- anonymous, guest, student, faculty, admin
--
CREATE TABLE Role (
  role_id INTEGER PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  rank INTEGER NOT NULL DEFAULT 0
);

--
-- A Course corresponds to a set of editable pages, assignments, and work, 
-- with faculty and students assigned to it through Registration entries.
--   * Its 'path' column gives the location of its 
--     root folder within the pages_os_root folder
--   * start_date sets which semester it's in.
--     (ignoring the 'end_date' and 'active' fields)
--   * The assignments_md5 keeps track of whether or not the corresponding
--     assignments.wiki file has been modified.
--   * The name_as_title column is for a display variation of the course name.
--   * The 'notes' column is for future use.
--
CREATE TABLE Course (
  course_id INTEGER PRIMARY KEY NOT NULL ,
  name TEXT NOT NULL,
  name_as_title TEXT NOT NULL DEFAULT '',
  path TEXT UNIQUE NOT NULL,
  start_date TEXT NOT NULL DEFAULT '1900-01-01',
  end_date TEXT NOT NULL DEFAULT '1901-01-01',
  assignments_md5 TEXT NOT NULL DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1,
  credits INTEGER NOT NULL DEFAULT 0,
  notes TEXT NOT NULL DEFAULT ''
);

-- Speed selects at the cost of slowing table modifications.
CREATE UNIQUE INDEX course_path_index ON Course (path);

--
-- A Registration ties together a person, a course, and a role, 
--  e.g. "john smith is a student in calculus"
--  Other fields :
--    date    : of this registration (pretty much unused)
--    midterm : grade, eg 'S', 'S-' etc
--    grade   : final course grade, eg 'A', 'WP', etc
--    credits : if different for this student than the course default
--    status  : any other info, eg 'withdrawn', 'audit', etc
CREATE TABLE Registration (
  registration_id INTEGER PRIMARY KEY NOT NULL ,
  person_id INTEGER NOT NULL DEFAULT 0
    CONSTRAINT fk_person_person_id REFERENCES Person(person_id),
  course_id INTEGER NOT NULL DEFAULT 0
    CONSTRAINT fk_course_course_id REFERENCES Course(course_id),
  role_id INTEGER NOT NULL DEFAULT 0
    CONSTRAINT fk_role_role_id REFERENCES Role(role_id),
  date TEXT,
  midterm TEXT NOT NULL DEFAULT '',
  grade TEXT NOT NULL DEFAULT '',
  credits INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT ''
);

--
-- An Assignment is anything that gets graded, including tests.
-- Faculty assign 'em ("Read this; write that") and grade 'em.
-- The "nth" field allows sorting them in the same order they're listed
-- in course_name/special/assignments.wiki
-- The "notes" field is (again) for possible future expansion
--
CREATE TABLE Assignment (
  assignment_id INTEGER PRIMARY KEY NOT NULL ,
  course_id INTEGER NOT NULL DEFAULT 0
    CONSTRAINT fk_course_course_id REFERENCES Course(course_id),
  name TEXT NOT NULL DEFAULT '',
  uriname TEXT NOT NULL DEFAULT '',
  due TEXT,
  nth INTEGER,
  blurb TEXT NOT NULL DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1,
  notes TEXT NOT NULL DEFAULT ''
);

--
-- Work is a what a student submits (or uploads) for an Assignment,
-- or where faculty comment on what the student has done.
-- Each corresponds to a wiki page that only one student and the faculty
-- can see, namely course_name/students/username/assignment_uriname.wiki
-- The 'submitted' field holds the 
-- DATETIME (in mysql is e.g. "2001-11-02 13:22:01") 
-- that the work was submitted; 
-- an empty string means the student hasn't submitted anything yet.
-- (At the moment I'm storing all times in the local timezone,
-- even though that's not part of the mysql datetime string.)
-- The "notes" field is for possible future expansion.
--
CREATE TABLE Work (
  work_id INTEGER PRIMARY KEY NOT NULL ,
  person_id INTEGER NOT NULL DEFAULT 0
   CONSTRAINT fk_person_person_id REFERENCES Person(person_id),
  assignment_id INTEGER NOT NULL DEFAULT 0
   CONSTRAINT fk_assignment_assignment_id REFERENCES Assignment(assignment_id),
  submitted TEXT NOT NULL DEFAULT '',
  studentLastSeen TEXT NOT NULL DEFAULT '',
  studentLastModified TEXT NOT NULL DEFAULT '',
  facultyLastSeen TEXT NOT NULL DEFAULT '',
  facultyLastModified TEXT NOT NULL DEFAULT '',
  grade TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT ''
);

--
-- Directory represents a disk folder,
-- including which course it's in and its permissions.
-- Its 'path' column gives its location with the pages_os_root folder,
-- which matches the notion of 'path' within the Course table.
--
CREATE TABLE Directory (
  directory_id INTEGER PRIMARY KEY NOT NULL,
  course_id INTEGER NOT NULL DEFAULT 0
   CONSTRAINT fk_course_course_id REFERENCES Course(course_id),
  path TEXT UNIQUE NOT NULL DEFAULT '',
  parent_id INTEGER DEFAULT NULL
   CONSTRAINT fk_parent_directory_id REFERENCES Directory(directory_id)
);

-- Speed selects at the cost of slowing table modifications.
CREATE UNIQUE INDEX directory_path_index ON Directory (path);

--
-- Permission enables read and/or write access to Directories.
--   rights : 3 => write & read access ; 1 => read access 
--   for either a person or a role. 
--   (admin & faculty have read/write always, if without a Permission)
--   non-admin, non-faculty folks need an explicit read or write permission,
--   otherwise they should be denied access.
--
CREATE TABLE Permission (
 permission_id INTEGER PRIMARY KEY NOT NULL,
 rights INTEGER NOT NULL DEFAULT 0,
 write INTEGER NOT NULL DEFAULT 0,
 directory_id INTEGER NOT NULL DEFAULT 0
   CONSTRAINT fk_directory_directory_id REFERENCES Directory(directory_id)
   ON DELETE CASCADE,
 role_id INTEGER DEFAULT NULL
   CONSTRAINT fk_role_role_id REFERENCES Role(role_id),
 person_id INTEGER DEFAULT NULL
   CONSTRAINT fk_person_person_id REFERENCES Person(person_id)
);
