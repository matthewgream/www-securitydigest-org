#!/usr/bin/perl

################################################################################
# $Id: feedback.cgi,v 1.2 2003/12/06 18:28:38 matt Exp $
################################################################################

{ $0 =~ /(.*)(\\|\/)/; push @INC, $1 if $1; }
use lib qw(.);
use CGI qw(nph);
use CGI::Carp qw(fatalsToBrowser);
use Socket;
use cgi_buffer;
$|=1;


################################################################################
# application constants
################################################################################

my $VERSION = "1.1";
my $SENDMAIL = "/usr/lib/sendmail -t";


################################################################################
# mail configurables
################################################################################

my $MAIL_TITLE 	  = "Curator of the 'Security Digest' Archives (TM)";
my $MAIL_ADDR  	  = "curator\@securitydigest.org";
my $SITE_TITLE    = "The 'Security Digest' Archives";
my $SITE_ADDR     = "feedback\@securitydigest.org";

require 'feedback.conf';

my $MAIL_FROM     = "$SITE_ADDR (Feedback CGI V$VERSION)";
my $MAIL_TO       = "$MAIL_ADDR ($MAIL_TITLE)";
my $MAIL_DATE     = gmtime;
my $MAIL_SUBJECT  = "Feedback";
my $MAIL_PREAMBLE = "$SITE_TITLE : Feedback";


################################################################################
# html configurables
################################################################################

my $PAGE_HEADER = "feedback_head.htm";
my $PAGE_FOOTER = "feedback_foot.htm";


################################################################################
# compose/send configurables
################################################################################

my $COMPOSE_HEADER = "
	Compose for: <span style=\"color:#999999;font-weight:bold;\">$MAIL_TITLE</span>";
my $COMPOSE_FOOTER = "
	You might like to include your address for a reply.";
my $SEND_HEADER = "
	Posted to: <span style=\"color:#999999;font-weight:bold;\">$MAIL_TITLE</span>";
my $SEND_FOOTER = "
	Your message will be read within 28 days, and dealt with appropriately.";


################################################################################
# instance information
################################################################################

my $cgi = new CGI;

my $script_name = "http://" . $cgi->virtual_host() . $cgi->script_name();
my $script_referer = $cgi->referer();
my $script_remote_agent = $cgi->user_agent();
	my $host_a = $ENV{REMOTE_ADDR};
	my $host_n = gethostname_local($host_a);
my $script_remote_host = $host_n . " [" . $host_a . "]";


################################################################################
# do the header
################################################################################

print $cgi->header('text/html');
print page_load($PAGE_HEADER);


################################################################################
# do the body - deliver or compose
################################################################################

my $script_body = $cgi->param('b');
if (defined $script_body)
  {
    print "
<H2>$SEND_HEADER</H2>
<P>$SEND_FOOTER</P>
";
	if(open(MAIL, "|$SENDMAIL"))
	  {
		print MAIL "To: $MAIL_TO\n";
		print MAIL "From: $MAIL_FROM\n";
		print MAIL "Subject: $MAIL_SUBJECT - $script_remote_host\n";
		print MAIL "X-Mailer: Feedback CGI V$VERSION\n";
		print MAIL "Content-type: text/plain\n\n";

		print MAIL "\n$MAIL_PREAMBLE\n" if ($MAIL_PREAMBLE);

		print MAIL "\nFeedback from:\n";
		print MAIL ": Host -  $script_remote_host\n";
		print MAIL ": Agent - $script_remote_agent\n";
		
		print MAIL "\nFeedback data:\n";
		foreach my $l (split('[\r\n]', $script_body)) {
		    print MAIL ": ", $l, "\n";
 	  	  }
		print MAIL "\n--\nDelivered by Feedback CGI V$VERSION\n";
		print MAIL "\n";
		close MAIL;
	  }
	else
	  {
		print "<P>Feedback could not be delivered: transport failure ($!).</P>";
	  }
  }
else
  {
    print "
<H2>$COMPOSE_HEADER</H2>
<TABLE style=\"width:100%;border-collapse:collapse;\"><TR><TD>
<FORM METHOD=\"POST\" ACTION=\"$script_name\">
<TABLE STYLE=\"width:500px;\" BORDER=\"0\" CELLSPACING=\"0\" CELLPADDING=\"1\">
  <TR><TD STYLE=\"background:#505050;\">
    <TABLE STYLE=\"width:100%;text-align:center;\" BORDER=\"0\" CELLSPACING=\"0\" CELLPADDING=\"5\">
      <TR><TD STYLE=\"text-align:center;background:#eeeeee;\">
        <TEXTAREA NAME=\"b\" COLS=\"64\" ROWS=\"12\"></TEXTAREA>
      </TD></TR>
      <TR><TD STYLE=\"text-align:left;background:#eeeeee;vertical-align:middle;\">
        <INPUT TYPE=\"submit\" VALUE=\"Send\">
      </TD></TR>
    </TABLE>
  </TD></TR>
  <TR><TD STYLE=\"font-size:64%;\">
      Source: $script_remote_host
  </TD></TR>
</TABLE>
</FORM>
</TD></TR></TABLE>
<P>$COMPOSE_FOOTER</P>
";
  }


################################################################################
# do the footer
################################################################################

print page_load($PAGE_FOOTER);


################################################################################
# finished
################################################################################

exit 0;


################################################################################
# get host name from ip address
################################################################################

sub gethostname_local
  {
	my ($a) = @_;
	my $h = gethostbyaddr(inet_aton($a), AF_INET);
	return $h if ($h);
	return $a;
  }


################################################################################
# load page information and return
################################################################################

sub page_load
  {
	my ($filename) = @_;
	my ($content) = "";
	if ( open (FILE, "<$filename") ) {
		while (<FILE>) { $content .= $_; }
		close (FILE);
	}
	return $content;
  }


################################################################################

1;

