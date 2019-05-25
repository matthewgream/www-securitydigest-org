#!/usr/bin/perl

################################################################################
# $Id: display.cgi,v 1.3 2003/04/11 13:35:23 securitydigest Exp $
################################################################################

{ $0 =~ /(.*)(\\|\/)/; push @INC, $1 if $1; }
use lib qw(.);
use CGI qw(nph);
use CGI::Carp qw(fatalsToBrowser);
use Socket;
use File::Basename;
use Compress::Zlib;
use cgi_buffer;
$|=1;


################################################################################
# definitions
################################################################################

my $PROGRAM = "Display CGI";
my $VERSION = "1.0";
my $AUTHOR  = "n/a";
my $VERBOSE = 0;


################################################################################
# configuration
################################################################################

my $LEADING   = "/home/content/68/3433068/html";
my $CONFIGURE = "$LEADING/cgi/display/display.conf";
my @INCLUDES  = ();
my %CONTENTS  = { };
my @MEDIA     = ();
my $PREFIX    = "";
my $VIRTUAL   = "";
if (open (FILE, "<$CONFIGURE"))
{
	while (<FILE>)
	{
		if (/^[ \t]*include[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "including $1\n" if ($VERBOSE);
			push @INCLUDES, $1;
		}
		if (/^[ \t]*media[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "media $1\n" if ($VERBOSE);
			push @MEDIA, $1;
		}
		if (/^[ \t]*prefix[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "prefix $1\n" if ($VERBOSE);
			$PREFIX = $1;
		}
		if (/^[ \t]*virtual[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "virtual $1\n" if ($VERBOSE);
			$VIRTUAL = $1;
		}
		if (/^[ \t]*header[ \t]*([^ \t]*)[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "header[$1] = $2\n" if ($VERBOSE);
			$CONTENTS{"header-$1"} = $2;
		}
		if (/^[ \t]*footer[ \t]*([^ \t]*)[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "footer[$1] = $2\n" if ($VERBOSE);
			$CONTENTS{"footer-$1"} = $2;
		}
		if (/^[ \t]*error[ \t]*([^ \t]*)[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "error[$1] = $2\n" if ($VERBOSE);
			$CONTENTS{"error-$1"} = $2;
		}
		if (/^[ \t]*format[ \t]*([^ \t]*)[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "format[$1] = $2\n" if ($VERBOSE);
			$CONTENTS{"format-$1"} = $2;
		}
		if (/^[ \t]*index[ \t]*([^ \t]*)[ \t]*([^ \n\t]*)[ \t\n]*/i) {
			print "index[$1] = $2\n" if ($VERBOSE);
			$CONTENTS{"index-$1"} = $2;
		}
	}
}

sub config_page_get
{
	my($n,$t) = @_;
	return $CONTENTS{"$n-$t"};
}
sub config_include_check
{ 
	my($f) = @_;
  	foreach (@INCLUDES) { if ($f =~ m/^$_$/) { return 1; } }
  	return 0;
}
sub config_media_check
{ 
	my($m) = @_;
  	foreach (@MEDIA) { if ($m eq $_) { return 1; } }
  	return 0;
}
sub config_params_load
{
	my($f,$p,$ff,$c) = @_;
	my($s) = $PREFIX . $VIRTUAL;
	$$p{'url'} = $PREFIX . $f;
	$$p{'url_textplain'} = "$s?f=$f\&amp\;t=text/plain";
	$$p{'url_texthtml'} = "$s?f=$f\&amp\;t=text/html";
	my(@v) = ();
	if (open FILE, "<$c")
	{
		while (<FILE>)
		{
			if (/^[ \t]*\#[ \t]*([^ \t]+)[ \t]+(.*)[ \t]*$/)
			{
				$$p{ lc($1) } = $2;
			}
			elsif (!scalar(@v))
			{
				foreach (split(/[ \t]*\|[ \t]*/,$_))
				{
					chomp;
					push @v, $_;
				}
			}
			elsif (/^[ \t]*$ff[ \t]*\|/i)
			{
				my(@vv) = @v;
				foreach (split(/[ \t]*\|[ \t]*/,$_))
				{
					chomp;
					$$p{ shift @vv } = $_;
				}
			}
		}
	}
}


################################################################################
# page setup - environment
################################################################################

my $cgi = new CGI;

my $ERROR_INVALID_MEDIA = "Invalid media: ";
my $ERROR_INVALID_FILE = "Invalid file: ";


################################################################################
# page processing - get, check and show
################################################################################

my $type = $cgi->param('t');
$type = "text/html" if (not defined $type);
print "type => $type\n" if ($VERBOSE);

my $file = $cgi->param('f');
$file = "undefined" if (not defined $file);
print "file => $file\n" if ($VERBOSE);

my $name = $cgi->param('n');
$name = "undefined" if (not defined $name);
print "name => $name\n" if ($VERBOSE);

config_media_check($type) 
	|| ( page_error("text/html", $file, $ERROR_INVALID_MEDIA . $type . " (media check failed) ") && exit 0 );
config_include_check($file) 
	|| ( page_error($type, $file, $ERROR_INVALID_FILE . $file . " (include check failed) ") && exit 0 );
my ($size, $mtime);
page_check_stats($file, \$size, \$mtime) 
	|| ( page_error($type, $file, $ERROR_INVALID_FILE . $file . " (page check failed) ")  && exit 0 );

my %param = { };
$param{'title'} = basename($file);
$param{'size'} = "$size";
$param{'mtime'} = "$mtime";
$param{'name'} = "$name";
$param{'root'} = dirname($file);
$param{'base'} = basename($file); $param{'base'} =~ s/\.[^\.]*$//g;

my $indx = $cgi->param('i');
$indx = dirname($file) . "/" . config_page_get("index", $type) if (not defined $indx);
$indx = $LEADING . "/" . $indx;
print "indx => $indx\n" if ($VERBOSE);
$param{'indx'} = "$indx";

config_params_load($file, \%param, basename($file), $param{'indx'});

print "base => $param{'base'}\n" if ($VERBOSE);
print "name => $param{'name'}\n" if ($VERBOSE);
print "title => $param{'title'}\n" if ($VERBOSE);
print "file => $param{'file'}\n" if ($VERBOSE);
print "url => $param{'url'}\n" if ($VERBOSE);
print "date => $param{'date'}\n" if ($VERBOSE);
print "size => $param{'size'}\n" if ($VERBOSE);
print "indx => $param{'indx'}\n" if ($VERBOSE);

page_print($type, $file, \%param);
exit 0;


################################################################################
# page rendering - high level mechanisms and wrappers
################################################################################

sub page_error
{
	my($type,$file,$error) = @_;
	my($type,$file,$error) = @_;
	my(%param) = {};
	$param{'title'} = $file;
	$param{'error'} = $error;
	print $cgi->header(-type => config_page_get("format", $type));
	print page_get_cast($type, "header", \%param);
	print page_get_cast($type, "error", \%param);
	print page_get_cast($type, "footer", \%param);
}
sub page_print
{
	my($type,$file,$param) = @_;
	my($data) = page_get_load($type, $file, \%param);
	print $cgi->header(-type => config_page_get("format", $type), -last_modified => scalar localtime $$param{'mtime'} );
	print page_get_cast($type, "header", \%param);
	print $data;
	print page_get_cast($type, "footer", \%param);
}

sub page_get_cast
{
	my($type,$code,$param) = @_;
	my($name) = config_page_get($code, $type);
	if ($name && page_check_exist($name)) {
		return page_cast($name, \%param);
	}
	return "";
}
sub escape_html
{
	my($s) = @_;
    for ($s) {
        s/&/&amp;/g;
        s/</&lt;/g;
        s/>/&gt;/g;
        s/"/&quot;/g;
    }
	return $s;
}
sub page_translate_text_html
{
	my($s,$p) = @_;
	return escape_html($s);
}
sub page_translate_text_direct
{
	my($s,$p) = @_;
	my($tf) = 0; my($ts) = 0; my($td) = "";

	my($r) = "<pre>";
	$r .= sprintf("%16s  %10s  %s", "----------------", "----------", "------------------------");
	$r .= "\n";
	for my $l (sort split("\n", $s)) {
		my(@x) = split (",", $l);
		next if ($x[1] eq '..' && $$p{'name'} eq "");
		next if ($x[1] eq '.');

		my($ff) = escape_html($x[1]); $ff .= "/" if ($x[0] =~ m/d/);
		my($fu) = escape_html($x[1]); $fu .= "/" if ($x[0] =~ m/d/);
		$fu = "/".$$p{'root'}."/" if ($x[1] eq '..');
		my($fs) = escape_html($x[2]);
		my($fd) = escape_html($x[3]);
		$r .= sprintf("%16s  %10s  <a href=\"%s\">%s</a>\n", $fd, $fs, $fu, $ff);
		$tf += 1;
		$ts += $x[2];
		$td =  $x[3] if ($x[3] > $td);
    }
	$r .= sprintf("%16s  %10s  %s", "----------------", "----------", "------------------------");
	$r .= "</pre>\n";

	$$p{'mirror_path'} = $$p{'name'};# $$p{'mirror_path'} =~ s,^/,,;
	$$p{'mirror_file'} = $tf;
	$$p{'mirror_byte'} = $ts;
	$$p{'mirror_date'} = $td;

	return $r;
}
sub page_translate_text_rfc822
{
	my($s,$p) = @_;
	my($t) = "";
	my($h) = 1;
	foreach my $l (split('\n', $s)) 
	{
		if ($h > 0) {
			if ($l =~ m/^$/) {
				$h = 0;
			} else {
				if ($l =~ m/^([^:]*): (.*)$/) {
					my($n) = $1;
					my($v) = $2;
					if ($v =~ m/\d\d\d/ && $n =~ m/X-(Message|Thread)-(Next|Prev|Index)/) {
						$n = "Refer$1$2";
						$v = "[$1 $2: <a href=\"$v\">$v</a>]";
					} else {
						$v = escape_html($v);
					}
					$$p{"rfc822_$n"} = $v;
					print "rfc822_$n => $v\n" if ($VERBOSE);
				}
			}
		} else {
			$t .= escape_html($l) . "\n";
		}
	}
	return $t;
}
sub page_translate_text_rfc822_archive
{
	my($s,$p) = @_;
	my($t) = "";
	my($h) = 0; 
	my(%vl); my($vp) = "";
	my($cnt_cur) = 0; my($cnt_end) = 0;
	$cnt_end = () = $s =~ /----MESSAGE-BEGIN/g;
	foreach my $l (split('\n', $s)) 
	{
		if ($l =~ m/^----MESSAGE-BEGIN/) {
			$h = 1;
			%vl = ( );
			$vp = "";
			if ($l =~ m/\<([\d]+)\>[ \t]*$/) {
				$t .= "<a name=\"$1\"></a>";
			}
			$t .= "<a name=\"" . sprintf("%06d", $cnt_cur) . "\"></a>";
		} elsif ($l =~ m/^----MESSAGE-END/) {
			if ($h == 0) { 
				$t .= "</pre>";
			}
			$cnt_cur++;
		} else {
			if ($h == 1) {
				if ($l =~ m/^$/) {
					$h = 0;
					$t .= "<span style=\"font-weight:bold;\"><pre>";
					$t .= "-----------";
					$t .= "[" . sprintf("%06d", $cnt_cur) . "]";
					$t .= "<a href=\"#" . sprintf("%06d", $cnt_cur+1). "\">[next]</a>" if ($cnt_cur < ($cnt_end - 1));
				 	$t .= "[next]" if ($cnt_cur == ($cnt_end - 1));
					$t .= "<a href=\"#" . sprintf("%06d", $cnt_cur-1). "\">[prev]</a>" if ($cnt_cur > 0);
					$t .= "[prev]" if ($cnt_cur == 0);
					$t .= "<a href=\"#" . sprintf("%06d", $cnt_end-1). "\">[last]</a>" if ($cnt_cur < ($cnt_end - 1));
				 	$t .= "[last]" if ($cnt_cur == ($cnt_end - 1));
					$t .= "<a href=\"#" . sprintf("%06d", 0) .         "\">[first]</a>" if ($cnt_cur > 0);
					$t .= "[first]" if ($cnt_cur == 0);
					$t .= "----------------------------------------------------\n";
					my(@vx);
					push @vx, $vl{"date"} if (exists $vl{"date"});
					push @vx, $vl{"from"} if (exists $vl{"from"});
					push @vx, $vl{"to"} if (exists $vl{"to"});
					push @vx, $vl{"cc"} if (exists $vl{"cc"});
					push @vx, $vl{"subject"} if (exists $vl{"subject"});
					$t .= join("\n", @vx);
					$t .= "</pre></span><pre>";
				} else {
					if ($l =~ m/^(date|from|to|cc|bcc|subject|newsgroups)[ \t]*:[ \t]*(.*)$/i) {
						$vp = lc($1); my($vq) = $2; $vq =~ s/[ \t]*$//g;
						$vp = "to" if ($vp eq "newsgroups");
						if (exists $vl{$vp}) {
							$vl{$vp} .= "," if ($vl{$vp} !~ m/,[ \t]*/g);
							$vl{$vp} .= " ";
						} else {
							$vl{$vp} = sprintf ("%-10s ", ucfirst("$vp:"));
						}
						$vl{$vp} .= escape_html($vq);
					} elsif ($vp ne "" && $l =~ m/^[ \t]+(.*)$/) {
						my($vq) = $1; $vq =~ s/[ \t]*$//g;
						if (exists $vl{$vp}) {
							$vl{$vp} .= "," if ($vl{$vp} !~ m/,[ \t]*/g);
							$vl{$vp} .= " ";
						}
						$vl{$vp} .= escape_html($vq);
					} else {
						$vp = "";
					}
				}
			}
			if ($h == 0) {
				$t .= escape_html($l) . "\n";
			}
		}
	}
	$$p{"count"} = $cnt_end;
	return $t;
}
sub page_get_load
{
	my($type,$name,$param) = @_;
	if ($name && page_check_exist($name)) 
	{
		my $data = page_load($name);
		if ($type eq "text/html")
		{
			$data = page_translate_text_html($data,$param);
		}
		elsif ($type eq "text/rfc822")
		{
			$data = page_translate_text_rfc822($data,$param);
		}
		elsif ($type eq "text/rfc822-archive")
		{
			$data = page_translate_text_rfc822_archive($data,$param);
		}
		elsif ($type eq "text/direct")
		{
			$data = page_translate_text_direct($data,$param);
		}
		return $data;
	}
	else
	{
		return "ERROR";
	}
}

################################################################################
# page accessing - load or cast raw contents, including directories
################################################################################

sub page_check_exist
{
	my($file) = @_;
	return 1 if (-f "$LEADING/$file.gz");
	return 1 if (-f "$LEADING/$file");
	return 1 if (-d "$LEADING/$file");
	return 0;
}
sub page_check_stats
{
	my($file,$size,$date) = @_;
	my(@s) = stat("$LEADING/$file.gz");
	@s = stat("$LEADING/$file") if (!defined @s);
	return 0 if (!defined @s);
	$$size = @s[7];
	$$date = @s[9];
	return 1;
}
sub page_load
{
	my ($file) = @_;
	my ($data) = "";
	if (opendir(DH, "$LEADING/$file"))
	{
		foreach my $name (readdir(DH)) 
		{
        	(undef, undef, undef, undef, undef, undef, undef,
                $size, undef, $modified, undef, undef, undef) = stat("$LEADING/$file/$name");
            ($min, $hr, $day, $mon, $yr) = (localtime($modified))[1,2,3,4,5];
        	$yr += 1900    unless $yr > 1900;
        	my($date) = sprintf("%04d-%02d-%02d %02d:%02d", $yr, $mon, $day, $hr, $min);

        	if (-d "$LEADING/$file/$name") {
				$data .= "d,$name,$size,$date\n";
        	} else {
				$data .= "f,$name,$size,$date\n";
        	}
        }
		closedir(DH);
	}
	elsif (my $gz = gzopen("$LEADING/$file.gz", "rb"))
	{
		my $gb;
		while ($gz->gzread($gb) > 0) { 
			$data .= $gb;
		}
		$gz->gzclose();
	}
	elsif (open(FH,"<$LEADING/$file"))
	{
		while (<FH>) {
			$data .= $_;
		}
		close(FH);
	} 
	return $data;
}
use cgi_template;
sub page_cast
{
	my ($file, $cast) = @_;
	my ($page) = new cgi::template("$LEADING/$file");
	my ($data) = $page->cast(\%$cast);
	return $data;
}

################################################################################

1;

