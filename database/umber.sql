----------------------------------------
-- umber.sql
--
--   umber database definitions for sqlite3 database
--
--       Person
--       Role	
--       Course
--       Page                FK Course
--       Assignment          FK Course, FK Page
--       Registration        FK Person, FK Course, FK Role
--       Work 		     FK Person, FK Assignment, FK Page
--
--   To create the database :          ./init_db
--   To create & populate it:          ./reset_db
--   To create an ERD diagram of it:   ./erd/make_png

-- In the previous wikiacademia system, authentication
-- was by either password or ldap_id. Here it's just password.
--
CREATE TABLE Person (
  person_id INTEGER PRIMARY KEY NOT NULL,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL DEFAULT '',
  name TEXT NOT NULL DEFAULT '',
  email TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT ''
);

-- Speed select statements at the cost of slowing table modifications.
CREATE UNIQUE INDEX person_username_index ON Person (username);

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
--     top folder within the courses_os_base folder (e.g. 'courses')
--     for example 'demo' for the demo course 
--     which is at /<os_root>/<courses_os_base>/demo
--     e.g. /Users/mahoney/academics/umber/courses/demo
--   * start_date sets which semester it's in.
--     (ignoring the 'end_date' and 'active' fields)
--   * The assignments_md5 keeps track of whether or not the corresponding
--     assignments.wiki file has been modified.
--   * The name_as_title column is for a display variation of the course name.
--   * The 'notes' column is for future use.
--
CREATE TABLE Course (
  course_id INTEGER PRIMARY KEY NOT NULL,
  path TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  name_as_title TEXT NOT NULL DEFAULT '',
  start_date TEXT NOT NULL DEFAULT '1900-01-01',
  end_date TEXT NOT NULL DEFAULT '1901-01-01',
  assignments_md5 TEXT NOT NULL DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1,
  credits INTEGER NOT NULL DEFAULT 0,
  notes TEXT NOT NULL DEFAULT ''
);

CREATE UNIQUE INDEX course_path_index ON Course(path);

--
-- A Page is one file or directory
--   * 'path' is its file & url , after host/url_base or os_base
--     for example http://localhost/umber/democourse/home
--     at /Users/mahoney/academics/umber/courses/democourse/home
--     would have as its path 'democourse/home'
--   * The content_hash is an md5 hash of the file contents,
--     used to see whether or not the corresponding file has changed.
--   * as_html is a cache of the processed file contents
--
CREATE TABLE Page (
  page_id INTEGER PRIMARY KEY NOT NULL,
  path TEXT UNIQUE NOT NULL,
  course_id INTEGER DEFAULT NULL
    CONSTRAINT fk_course_course_id REFERENCES Course(course_id),
  content_hash INTEGER DEFAULT 0,
  as_html TEXT DEFAULT '',
  notes TEXT DEFAULT ''
);

CREATE UNIQUE INDEX page_path_index ON Page(path);

--
-- A Registration ties together a person, a course, and a role, 
--  e.g. "john smith is a student in calculus"
--  Other fields :
--    date    : of this registration (pretty much unused)
--    midterm : grade, eg 'S', 'S-' etc
--    grade   : final course grade, eg 'A', 'WP', etc
--    credits : what this student is registered for in this course
--    status  : any other info, eg 'withdrawn', 'audit', etc
CREATE TABLE Registration (
  registration_id INTEGER PRIMARY KEY NOT NULL,
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
-- The "nth" field gives each a (1,2,3,...) number within one course.
-- The "notes" field is (again) for possible future expansion
--
CREATE TABLE Assignment (
  assignment_id INTEGER PRIMARY KEY NOT NULL,
  course_id INTEGER NOT NULL DEFAULT 0
    CONSTRAINT fk_course_course_id REFERENCES Course(course_id),
  nth INTEGER NOT NULL DEFAULT 1,
  name TEXT NOT NULL DEFAULT '',
  due TEXT,
  blurb TEXT NOT NULL DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1,
  notes TEXT NOT NULL DEFAULT ''
);

--
-- Work corresponds to a web page where a student submits their work
-- for an Assignment, and where faculty comments on and grades that work.
-- The web page can only be seen by that student and the faculty,
-- at <course_name>/students/<username>/<nth>.md .
-- The 'submitted' field holds the date that the work was submitted,
-- e.g. "2018-01-30T23:59:00-05:00".
-- An empty string means the student hasn't submitted anything yet.
-- Similarly, the *_seen and *_modified fields are the dates when
-- the work page was last seen and last modified.
-- The "notes" field is for possible future expansion.
--
CREATE TABLE Work (
  work_id INTEGER PRIMARY KEY NOT NULL,
  page_id INTEGER NOT NULL DEFAULT 0
   CONSTRAINT fk_page_page_id REFERENCES Page(page_id),
  person_id INTEGER NOT NULL DEFAULT 0
   CONSTRAINT fk_person_person_id REFERENCES Person(person_id),
  assignment_id INTEGER NOT NULL DEFAULT 0
   CONSTRAINT fk_assignment_assignment_id REFERENCES Assignment(assignment_id),
  submitted TEXT NOT NULL DEFAULT '',
  student_seen TEXT NOT NULL DEFAULT '',
  student_modified TEXT NOT NULL DEFAULT '',
  faculty_seen TEXT NOT NULL DEFAULT '',
  faculty_modified TEXT NOT NULL DEFAULT '',
  grade TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT ''
);

