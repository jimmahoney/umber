#!/usr/bin/env perl
#
# wikiacademia's database population
#
#
use strict;
use warnings;
use Wikiacademia;

print "    Calling Wikiacademia to create default course and users.\n";
print "    Making test data: demo course, janedoe, johnsmith, assignments.\n";

my $janedoe = Person->find_or_create({ username  => 'janedoe',
				       password  => 'test',
				       firstname => 'Jane',
				       lastname  => 'Doe',
				       name      => 'Jane Q. Doe',
				       email     => 'janedoe@fake.address',
				     });
my $johnsmith = Person->find_or_create({ username  => 'johnsmith',
					 password  => 'test',
					 firstname => 'John',
					 lastname  => 'Smith',
					 name      => 'Johnny Smith',
					 email     => 'johnsmith@fake.address',
				     });
my $tedteacher = Person->find_or_create({ username  => 'tedteacher',
					  password  => 'teach',
					  firstname => 'Theodore',
					  lastname  => 'Teacher',
					  name      => 'Ted Teacher',
				     });
my $democourse = Course->find_or_create({name       => 'Demo Course',
					 directory  => '/course_demo',
					 start_date => '2006-01-01',
					});
Registration->find_or_create({ person => $tedteacher,
			       course => $democourse,
			       role   => Role->faculty,
			       date   => '2005-01-12',
			     });
Registration->find_or_create({ person => $janedoe,
			       course => $democourse,
			       role   => Role->student,
			       date   => '2005-01-12',
			     });
Registration->find_or_create({ person => $johnsmith,
			       course => $democourse,
			       role   => Role->student,
			       date   => '2005-01-13',
			     });
Assignment->find_or_create({course  => $democourse,
			    nth     => 1,
			    name    => 'Week One test',
			    uriname => 'week_one_test',
			    due     => '2005-03-01',
			    blurb   => "#Read chapter blah\n#Do Exercise ..\n",
			   });
Assignment->find_or_create({course  => $democourse,
			    nth     => 2,
			    name    => 'Week Two test',
			    uriname => 'week_two_test',
			    due     => '2005-03-01',
			    blurb   => "Give Jim chocolate.\n",
			   });
Assignment->find_or_create({course  => $democourse,
			    nth     => 3,
			    name    => 'Week Three test',
			    uriname => 'week_three_test',
			    due     => '2005-04-01',
			    blurb   => "#Read ..\n# Do ..\n",
			   });

