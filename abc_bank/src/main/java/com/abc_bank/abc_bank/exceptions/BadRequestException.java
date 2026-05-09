package com.abc_bank.abc_bank.exceptions;

public class BadRequestException extends RuntimeException{
  public BadRequestException(String error){
    super(error);
  }
}
