package cgi::template;

use Exporter;
@ISA = qw(Exporter);
@EXPORT_OK = qw(cast cast_loop finalize html clear);

#use strict;
use vars qw($errstr);
$errstr = '';


sub new
  {
    my ($class, $file) = @_;
    my $self = {
		file => $file,
		template => '',
		template_copy => '',
	       };
    open(FILE, $file) or die "Cannot open file $file: $!";
    while(<FILE>)
      {
	$$self{template} .= $_;
	$$self{template_copy} .= $_;
      }
    close(FILE);
    bless $self, $class;
    return $self;
  }

sub clear {
  my ($self) = $_[0];
  $$self{template} = $$self{template_copy};

  return 1;
}

sub cast
  {
    my ($self, $hr) = @_;
    $$self{template}=~s/<!--\s*cgi:\s*(\S+?)(?:\((.*)\))?\s*-->/_exec_directive($hr, $1, $2)/ieg;
    return $$self{template};
  }

sub cast_loop
  {
    my ($self, $name, $ar, $finalize) = @_;
    $$self{template} =~ m/<!--\s*loop:\s*$name\s*-->(.*)<!--\s*end:\s*$name\s*-->/s;
    my $pattern = $1;
    my $pattern_copy = $pattern;
    my $out;
    foreach (@{$ar}) {
      $pattern = $pattern_copy;
      $pattern =~ s/<!--\s*item:\s*(\S+?)(?:\((.*)\))?\s*-->/_exec_directive($_, $1, $2)/ieg;
      $out.=$pattern;
    }
    if ($finalize) {
      $$self{template} =~ s/<!--\s*loop:\s*$name\s*-->.*<!--\s*end:\s*$name\s*-->/$out/s;
    } else {
      $$self{template} =~ s/(<!--\s*loop:\s*$name\s*-->).*(<!--\s*end:\s*$name\s*-->)/$out$1$pattern_copy$2/s;
    }
    return $$self{template};
  }

sub finalize
  {
    my ($self,$name) = @_;
    $$self{template} =~ s/<!--\s*loop:\s*$name\s*-->.*<!--\s*end:\s*$name\s*-->//s;
    return $$self{template};
  }

sub html 
  {
    my $self = $_[0];
    return $$self{template};
  }

sub _exec_directive
  {
    my ($hr, $directive, $args) = @_;
    if(ref($$hr{$directive}))
      {
	my $code = "\@a = ($args);";
	my @args = eval $code;
	return &{$$hr{$directive}}(@args);
      }
    else
      {
	return $$hr{$directive};
      }
  }

1;
